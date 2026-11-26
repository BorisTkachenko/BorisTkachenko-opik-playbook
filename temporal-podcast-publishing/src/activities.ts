import { activityInfo } from '@temporalio/activity';
import OpenAI from 'openai';
import './env';
import type { CdnUpload, EpisodeInput, ShowNotes } from './shared';

const MODEL = 'gpt-4o-mini';
const openai = new OpenAI();

async function chat(system: string, user: string, json = false): Promise<string> {
  const response = await openai.chat.completions.create({
    model: MODEL,
    messages: [
      { role: 'system', content: system },
      { role: 'user', content: user },
    ],
    ...(json ? { response_format: { type: 'json_object' as const } } : {}),
  });
  return response.choices[0]?.message?.content ?? '';
}

// --- Activity 1: show notes from the transcript (LLM) ------------------------

export async function draftShowNotes(episode: EpisodeInput): Promise<ShowNotes> {
  const content = await chat(
    'You write show notes for an indie podcast called "Burnt Toast & Backroads". ' +
      'Use only facts that appear in the transcript. Reply with JSON: ' +
      '{"summary": string (two sentences), "chapters": [{"timestamp": "mm:ss", "title": string}] (3 to 5), ' +
      '"links": string[] (only places or sites the guest actually names, otherwise an empty array)}.',
    `Episode ${episode.episodeId}: ${episode.title}\n\n${episode.transcript}`,
    true,
  );
  return JSON.parse(content) as ShowNotes;
}

// --- Activity 2: a social blurb built on the show notes (LLM) ----------------

export async function draftSocialBlurb(episode: EpisodeInput, notes: ShowNotes): Promise<string> {
  return await chat(
    'You write one social-media post announcing a new podcast episode. Warm, a little dry, ' +
      'under 240 characters, at most one emoji, no hashtags.',
    `Title: ${episode.title}\nSummary: ${notes.summary}`,
  );
}

// --- Activity 3: "upload to the CDN" that is flaky on purpose ----------------

// How many attempts fail before the CDN "recovers", per episode. Deterministic
// on purpose so every run tells the same story.
const FAILING_ATTEMPTS: Record<string, { count: number; message: string }> = {
  ep41: { count: 2, message: 'CDN edge returned 503 Service Unavailable (upload part 3 of 4)' },
  ep42: { count: 1, message: 'CDN upload failed: connection reset by peer' },
};

export async function uploadToCdn(episode: EpisodeInput, notes: ShowNotes, blurb: string): Promise<CdnUpload> {
  const { attempt } = activityInfo();
  const flaky = FAILING_ATTEMPTS[episode.episodeId];
  if (flaky && attempt <= flaky.count) {
    console.log(`[upload] ${episode.episodeId} attempt ${attempt} failed: ${flaky.message}`);
    throw new Error(flaky.message);
  }
  console.log(`[upload] ${episode.episodeId} attempt ${attempt} succeeded`);
  const bytes = Buffer.byteLength(JSON.stringify({ episode, notes, blurb }));
  return { url: `https://cdn.burnttoast.example/episodes/${episode.episodeId}/index.json`, bytes, attempt };
}
