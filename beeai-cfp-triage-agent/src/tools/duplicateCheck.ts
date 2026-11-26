// Tool 4: does this submission look like another one already in the pile?
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { getProposal, proposals, speakers } from "../data/store.ts";

const STOP = new Set(["the", "a", "an", "and", "of", "to", "in", "we", "our", "for", "that", "is", "how", "with", "on", "it", "at", "by"]);

const tokens = (s: string) =>
  new Set(s.toLowerCase().match(/[a-z0-9]+/g)?.filter((w) => !STOP.has(w)) ?? []);

export function jaccard(a: string, b: string): number {
  const x = tokens(a);
  const y = tokens(b);
  const shared = [...x].filter((w) => y.has(w)).length;
  const union = new Set([...x, ...y]).size;
  return union === 0 ? 0 : shared / union;
}

export function duplicateCheck(proposalId: string, threshold = 0.25) {
  const p = getProposal(proposalId);
  if (!p) return { error: `No proposal "${proposalId}".` };
  const name = (id: string) => speakers().find((s) => s.id === id)?.name ?? id;
  const matches = proposals()
    .filter((o) => o.id !== p.id)
    .map((o) => ({
      proposal_id: o.id,
      title: o.title,
      speaker: name(o.speaker_id),
      same_speaker: o.speaker_id === p.speaker_id,
      similarity: Math.round(jaccard(`${p.title} ${p.abstract}`, `${o.title} ${o.abstract}`) * 100) / 100,
    }))
    .filter((m) => m.similarity >= threshold)
    .sort((a, b) => b.similarity - a.similarity);
  return { proposal_id: p.id, possible_duplicate: matches.length > 0, matches };
}

export const duplicateCheckTool = new DynamicTool({
  name: "flag_duplicate",
  description:
    "Compare a proposal with every other submission and flag possible duplicates by text overlap (0-1 similarity). Input is the proposal id.",
  inputSchema: z.object({ proposal_id: z.string().describe("Proposal id such as P-1001") }),
  async handler(input) {
    return new JSONToolOutput(duplicateCheck(input.proposal_id));
  },
});
