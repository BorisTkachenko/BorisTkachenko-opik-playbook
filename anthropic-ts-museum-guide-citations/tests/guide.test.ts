import { describe, expect, it, vi } from "vitest";

// Stub the Anthropic client: no key and no network needed.
vi.mock("@anthropic-ai/sdk", () => ({
  default: class {
    messages = {
      create: async () => ({
        model: "claude-haiku-4-5-20251001",
        content: [{ type: "text", text: "Nine were saved. <quote>Nine of the eleven crew were saved.</quote>" }],
        usage: { input_tokens: 1700, output_tokens: 20 },
      }),
    };
  },
}));

describe("askGuide (traced, tracking disabled)", () => {
  it("still returns the model text when it is wrapped in track()", async () => {
    const { askGuide, NOTES } = await import("../src/guide.js");
    const { verifyQuotes } = await import("../src/notes.js");
    const answer = await askGuide("How many were saved?");
    expect(answer).toContain("Nine were saved");
    expect(verifyQuotes(answer, NOTES).every((c) => c.verbatim)).toBe(true);
  });
});
