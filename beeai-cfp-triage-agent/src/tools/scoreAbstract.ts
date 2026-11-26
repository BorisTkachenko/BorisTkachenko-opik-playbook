// Tool 3: score an abstract against its track's rubric. Deterministic, so the
// numbers the agent quotes are reproducible run to run.
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { getProposal, tracks } from "../data/store.ts";

const ACTIONABLE = ["attendees leave", "checklist", "demo", "dataset", "config", "queries", "show", "format"];
const HONEST = ["worse", "outage", "incident", "did not", "trade-off", "hid", "wrong", "failed", "cliff", "doubled"];

const hits = (text: string, words: string[]) => words.filter((w) => text.includes(w)).length;

export function scoreAbstract(proposalId: string) {
  const p = getProposal(proposalId);
  if (!p) return { error: `No proposal "${proposalId}".` };
  const track = tracks().find((t) => t.id === p.track);
  if (!track) return { error: `Proposal ${p.id} names unknown track "${p.track}".` };

  const text = `${p.title} ${p.abstract}`.toLowerCase();
  const numbers = (text.match(/\d+/g) ?? []).length;
  const breakdown = {
    topic_fit: Math.min(5, hits(text, track.rubric.keywords)),
    specifics: Math.min(5, numbers * 2),
    actionable_takeaways: Math.min(5, hits(text, ACTIONABLE) * 2),
    honesty_about_failures: Math.min(5, hits(text, HONEST) * 2),
  };
  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
  return {
    proposal_id: p.id,
    track: track.id,
    rubric_criteria: track.rubric.criteria,
    breakdown,
    total,
    max: 20,
  };
}

export const scoreAbstractTool = new DynamicTool({
  name: "score_abstract",
  description:
    "Score a proposal's abstract against its track rubric (topic fit, specifics, takeaways, honesty), 0-5 each, total out of 20. Input is the proposal id.",
  inputSchema: z.object({ proposal_id: z.string().describe("Proposal id such as P-1001") }),
  async handler(input) {
    return new JSONToolOutput(scoreAbstract(input.proposal_id));
  },
});
