import type { Proposal } from "../data/store.ts";

export function triagePrompt(p: Proposal): string {
  return `You are the first-pass reviewer for the Hollowbrook DevDays call for proposals.

For the proposal below, gather evidence and then decide ACCEPT, WAITLIST or REJECT. Before deciding you need four facts, each from a different tool: the speaker's record (speaker id), the open slots in the track (track id), the rubric score out of 20 (proposal id), and whether another submission overlaps this one (proposal id). Never invent scores, slots or history.

Rules of thumb: reject likely duplicates and abstracts scoring under 8; accept strong abstracts (14 or more) when a slot is open; waitlist good abstracts when the track is full or the speaker record is a concern.

Proposal ${p.id}
Title: ${p.title}
Speaker id: ${p.speaker_id}
Track: ${p.track}
Abstract: ${p.abstract}

Final answer format:
Recommendation: <accept | waitlist | reject>
Slot: <slot name or none>
Reasons: <2-4 short bullet points citing tool results>`;
}
