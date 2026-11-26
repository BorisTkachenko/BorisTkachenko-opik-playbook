import { describe, expect, it } from "vitest";
import { checkRules, countSentences, hasEmojiOrBang, parseReleaseNote } from "../src/rules.js";
import { formatChangeList, loadChangeLists } from "../src/changelogs.js";
import { PROMPT_V1, PROMPT_V2 } from "../src/prompts.js";

describe("rule checks", () => {
  it("splits a reply into headline and summary", () => {
    const note = parseReleaseNote("Headline: Added `tidepool doctor`\nSummary: One check for everything. Nothing breaks.");
    expect(note.headline).toBe("Added `tidepool doctor`");
    expect(countSentences(note.summary)).toBe(2);
  });

  it("flags emoji and exclamation marks", () => {
    expect(hasEmojiOrBang("Tidepool 3.6 is here! ")).toBe(true);
    expect(hasEmojiOrBang("Tidepool 3.6 🚀")).toBe(true);
    expect(hasEmojiOrBang("Tidepool 3.6 adds shell completions.")).toBe(false);
  });

  it("fails a hype-filled v1-style reply and passes a v2-style one", () => {
    const hype = "Headline: 🚀 Supercharge your sync!\nSummary: Upgrade today. It is game-changing. You will love it.";
    const plain = "Headline: `tidepool sync` is 3x faster on large repositories\nSummary: Sync speed triples above 10,000 files. The `--legacy-paths` flag is removed.";
    expect(checkRules(hype)).toEqual({ plainText: false, summaryShort: false });
    expect(checkRules(plain)).toEqual({ plainText: true, summaryShort: true });
  });
});

describe("data and prompts", () => {
  it("loads five change lists and renders them as bullets", () => {
    const entries = loadChangeLists();
    expect(entries).toHaveLength(5);
    expect(formatChangeList(entries[0]!)).toMatch(/^tidepool 3\.4\.0\n- Added/);
  });

  it("keeps the rules out of v1 and in v2", () => {
    expect(PROMPT_V1).not.toMatch(/exclamation/);
    expect(PROMPT_V2).toMatch(/no exclamation marks/);
    expect(PROMPT_V2).toMatch(/at most 2 sentences/);
  });
});
