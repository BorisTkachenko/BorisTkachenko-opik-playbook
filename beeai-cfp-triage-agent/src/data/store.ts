// Offline CFP data: JSON files under data/. Nothing here touches the network.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export type Talk = { year: number; title: string; rating: number };
export type Speaker = {
  id: string;
  name: string;
  affiliation: string;
  past_talks: Talk[];
  no_shows: number;
  code_of_conduct_flags: number;
};
export type Slot = { slot: string; status: "open" | "taken"; proposal_id: string | null };
export type Track = {
  id: string;
  name: string;
  chair: string;
  rubric: { keywords: string[]; criteria: string[] };
  slots: Slot[];
};
export type Proposal = {
  id: string;
  speaker_id: string;
  track: string;
  title: string;
  abstract: string;
};

function load<T>(file: string): T {
  const url = new URL(`../../data/${file}`, import.meta.url);
  return JSON.parse(readFileSync(fileURLToPath(url), "utf8")) as T;
}

export const speakers = (): Speaker[] => load<Speaker[]>("speakers.json");
export const tracks = (): Track[] => load<Track[]>("tracks.json");
export const proposals = (): Proposal[] => load<Proposal[]>("proposals.json");

export function getProposal(id: string): Proposal | undefined {
  return proposals().find((p) => p.id === id);
}
