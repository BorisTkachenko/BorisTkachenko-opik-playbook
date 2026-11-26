import { beforeEach, describe, expect, it, vi } from 'vitest';

// Activities read the attempt number from Temporal's activity context; stub it.
const info = { attempt: 1, activityType: 'x', workflowExecution: { workflowId: 'wf-test' } };
vi.mock('@temporalio/activity', () => ({ activityInfo: () => info }));

// A stubbed OpenAI client: no key, no network.
const create = vi.fn();
vi.mock('openai', () => ({ default: class { chat = { completions: { create } }; } }));

import { draftShowNotes, simulatedCdnFailure, uploadToCdn } from '../src/activities';
import type { EpisodeInput, ShowNotes } from '../src/shared';

const episode: EpisodeInput = { episodeId: 'ep41', title: 'T', transcript: '[00:00] hello' };
const notes: ShowNotes = { summary: 's', chapters: [], links: [] };

beforeEach(() => {
  info.attempt = 1;
  create.mockReset();
});

describe('simulated CDN outage', () => {
  it('fails the first attempts of each episode, then recovers', () => {
    expect(simulatedCdnFailure('ep41', 1)).toMatch(/503/);
    expect(simulatedCdnFailure('ep41', 2)).toMatch(/503/);
    expect(simulatedCdnFailure('ep41', 3)).toBeUndefined();
    expect(simulatedCdnFailure('ep42', 1)).toMatch(/connection reset/);
    expect(simulatedCdnFailure('ep42', 2)).toBeUndefined();
    expect(simulatedCdnFailure('unknown-episode', 1)).toBeUndefined();
  });
});

describe('uploadToCdn with Opik tracking disabled', () => {
  it('throws on a failing attempt even when it is traced', async () => {
    // The trace link makes the activity open (disabled, no-op) Opik spans; the wrapper must rethrow.
    const traced = { ...episode, trace: { traceId: '01a21728-fe99-72ec-92fb-7403b61c25ec', parentSpanId: '01a21728-fe99-72ec-92fb-7403b61c25ed' } };
    await expect(uploadToCdn(traced, notes, 'blurb')).rejects.toThrow(/503/);
  });

  it('returns the attempt that finally succeeded', async () => {
    info.attempt = 3;
    const result = await uploadToCdn(episode, notes, 'blurb');
    expect(result.attempt).toBe(3);
    expect(result.url).toContain('/episodes/ep41/');
  });
});

describe('draftShowNotes', () => {
  it('parses the model JSON and sends the transcript to the model', async () => {
    create.mockResolvedValue({ choices: [{ message: { content: JSON.stringify(notes) } }] });
    const result = await draftShowNotes(episode);
    expect(result).toEqual(notes);
    const sent = create.mock.calls[0][0];
    expect(sent.model).toBe('gpt-4o-mini');
    expect(sent.messages[1].content).toContain('[00:00] hello');
  });
});
