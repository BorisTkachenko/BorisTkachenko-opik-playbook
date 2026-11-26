// Tool 1: what do we know about this speaker from earlier editions?
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { speakers } from "../data/store.ts";

export function speakerHistory(speakerId: string) {
  const s = speakers().find((x) => x.id === speakerId);
  if (!s) return { error: `No speaker with id "${speakerId}".` };
  const ratings = s.past_talks.map((t) => t.rating);
  const avg = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
  return {
    speaker_id: s.id,
    name: s.name,
    affiliation: s.affiliation,
    past_talks: s.past_talks,
    average_rating: avg === null ? null : Math.round(avg * 100) / 100,
    no_shows: s.no_shows,
    code_of_conduct_flags: s.code_of_conduct_flags,
    first_time_speaker: s.past_talks.length === 0,
  };
}

export const speakerHistoryTool = new DynamicTool({
  name: "speaker_history",
  description:
    "Look up a speaker's record: past talks and ratings, no-shows, code-of-conduct flags. Input is the speaker id, e.g. S-201.",
  inputSchema: z.object({ speaker_id: z.string().describe("Speaker id such as S-201") }),
  async handler(input) {
    return new JSONToolOutput(speakerHistory(input.speaker_id));
  },
});
