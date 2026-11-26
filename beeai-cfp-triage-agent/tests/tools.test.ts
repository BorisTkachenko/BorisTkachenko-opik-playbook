import { describe, expect, it } from "vitest";
import { speakerHistory } from "../src/tools/speakerHistory.ts";
import { trackCapacity } from "../src/tools/trackCapacity.ts";
import { scoreAbstract } from "../src/tools/scoreAbstract.ts";
import { duplicateCheck } from "../src/tools/duplicateCheck.ts";
import { triagePrompt } from "../src/agent/prompt.ts";
import { getProposal } from "../src/data/store.ts";

describe("CFP tools", () => {
  it("summarises a returning speaker and flags a first-timer", () => {
    expect(speakerHistory("S-201")).toMatchObject({ average_rating: 4.75, first_time_speaker: false });
    expect(speakerHistory("S-202")).toMatchObject({ first_time_speaker: true, average_rating: null });
    expect(speakerHistory("S-999")).toHaveProperty("error");
  });

  it("counts only open slots", () => {
    expect(trackCapacity("platform")).toMatchObject({ open_count: 1, open_slots: ["Thu 14:00"] });
    expect(trackCapacity("ml")).toMatchObject({ open_count: 0 });
  });

  it("scores a concrete abstract above a vague one", () => {
    const strong = scoreAbstract("P-1001") as { total: number };
    const vague = scoreAbstract("P-1003") as { total: number };
    expect(strong.total).toBeGreaterThanOrEqual(14);
    expect(vague.total).toBeLessThan(8);
  });

  it("flags the near-duplicate pair across speakers and nothing else", () => {
    const dup = duplicateCheck("P-1005") as { possible_duplicate: boolean; matches: { proposal_id: string }[] };
    expect(dup.possible_duplicate).toBe(true);
    expect(dup.matches[0].proposal_id).toBe("P-1004");
    expect((duplicateCheck("P-1003") as { possible_duplicate: boolean }).possible_duplicate).toBe(false);
  });

  it("puts the proposal text into the prompt", () => {
    const prompt = triagePrompt(getProposal("P-1005")!);
    expect(prompt).toContain("Proposal P-1005");
    expect(prompt).toContain("Speaker id: S-206");
  });
});
