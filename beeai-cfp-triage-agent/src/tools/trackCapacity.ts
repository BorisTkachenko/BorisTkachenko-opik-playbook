// Tool 2: is there still room in the track the proposal was submitted to?
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { tracks } from "../data/store.ts";

export function trackCapacity(trackId: string) {
  const t = tracks().find((x) => x.id === trackId);
  if (!t) return { error: `No track "${trackId}". Valid: ${tracks().map((x) => x.id).join(", ")}.` };
  const open = t.slots.filter((s) => s.status === "open").map((s) => s.slot);
  return {
    track: t.id,
    name: t.name,
    chair: t.chair,
    total_slots: t.slots.length,
    open_slots: open,
    open_count: open.length,
  };
}

export const trackCapacityTool = new DynamicTool({
  name: "track_capacity",
  description:
    "Check how many schedule slots are still open in a track and which ones. Input is the track id (platform, ml, frontend, security).",
  inputSchema: z.object({ track: z.string().describe("Track id") }),
  async handler(input) {
    return new JSONToolOutput(trackCapacity(input.track));
  },
});
