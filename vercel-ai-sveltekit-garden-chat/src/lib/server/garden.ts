import fs from "node:fs";
import path from "node:path";

export interface GuideSection {
  title: string;
  body: string;
}

// Split the guide into "## heading" sections: the unit we retrieve.
export function parseGuide(markdown: string): GuideSection[] {
  return markdown
    .split(/^## /m)
    .slice(1)
    .map((chunk) => {
      const [title, ...rest] = chunk.split("\n");
      return { title: title.trim(), body: rest.join("\n").trim() };
    });
}

const STOP = new Set(
  "the a an and or of to in on for is are can i my it do does how what when should with at be if not you your".split(" "),
);

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter((w) => w.length > 2 && !STOP.has(w));
}

// Rank sections by how many distinct query words they contain (title hits count double).
export function retrieve(query: string, sections: GuideSection[], k = 2): GuideSection[] {
  const words = new Set(tokenize(query));
  return sections
    .map((section) => {
      const title = new Set(tokenize(section.title));
      const body = new Set(tokenize(section.body));
      let score = 0;
      for (const w of words) score += (title.has(w) ? 2 : 0) + (body.has(w) ? 1 : 0);
      return { section, score };
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((r) => r.section);
}

let cached: GuideSection[] | undefined;
export function loadGuide(): GuideSection[] {
  cached ??= parseGuide(fs.readFileSync(path.resolve(process.cwd(), "data/garden-guide.md"), "utf8"));
  return cached;
}

export const SYSTEM_PREAMBLE = `You are Sprout, the garden-care assistant for the Hollowbrook valley allotments.
Answer in two to four sentences, using ONLY the guide excerpts below. If the excerpts do not
cover the question, say plainly that the Hollowbrook guide does not cover it instead of guessing.`;

export function buildSystemPrompt(question: string, sections = loadGuide()): { system: string; used: string[] } {
  const hits = retrieve(question, sections);
  const excerpts = hits.length
    ? hits.map((s) => `### ${s.title}\n${s.body}`).join("\n\n")
    : "(no relevant excerpt found)";
  return { system: `${SYSTEM_PREAMBLE}\n\nGuide excerpts:\n${excerpts}`, used: hits.map((s) => s.title) };
}
