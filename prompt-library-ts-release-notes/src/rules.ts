/** Deterministic checks that mirror the rules in prompt v2. The Opik suite judges the same rules with an LLM. */

export interface ReleaseNote {
  headline: string;
  summary: string;
}

/** Split a "Headline: ...\nSummary: ..." reply into its two parts. */
export function parseReleaseNote(text: string): ReleaseNote {
  const headline = /^\s*headline:\s*(.+)$/im.exec(text)?.[1]?.trim() ?? "";
  const summary = /^\s*summary:\s*([\s\S]+)$/im.exec(text)?.[1]?.trim() ?? "";
  return { headline, summary };
}

const EMOJI = /\p{Extended_Pictographic}/u;
const HYPE = /revolutionary|game[- ]chang|supercharg|blazing/i;

export function hasEmojiOrBang(text: string): boolean {
  return EMOJI.test(text) || text.includes("!");
}

export function hasHypeWords(text: string): boolean {
  return HYPE.test(text);
}

/** Count sentences by terminal punctuation followed by space or end of text. */
export function countSentences(text: string): number {
  return (text.match(/[.!?]+(?=\s|$)/g) ?? []).length;
}

export function checkRules(text: string): { plainText: boolean; summaryShort: boolean } {
  const note = parseReleaseNote(text);
  return {
    plainText: !hasEmojiOrBang(text) && !hasHypeWords(text),
    summaryShort: countSentences(note.summary) <= 2 && note.summary.length > 0,
  };
}
