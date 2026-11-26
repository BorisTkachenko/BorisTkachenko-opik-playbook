import { describe, expect, it } from "vitest";
import type { Opik } from "opik";
import { loadChangeLists } from "../src/changelogs.js";
import { makeReleaseNoteWriter } from "../src/traced.js";
import type { ChatClient } from "../src/writer.js";

// Runs with OPIK_TRACK_DISABLE=true (see `npm test` in the README): track() then calls the
// wrapped function as-is, so nothing is sent to Opik and no server is needed.
describe("tracked writer with tracking disabled", () => {
  it("fetches the pinned prompt version and returns the model text", async () => {
    const asked: Array<{ name: string; version?: string }> = [];
    const opik = {
      getPrompt: async (o: { name: string; version?: string }) => {
        asked.push(o);
        return { prompt: "SYSTEM RULES", commit: "abc12345" };
      },
    } as unknown as Opik;
    const seen: unknown[] = [];
    const stub = {
      chat: {
        completions: {
          create: async (req: { messages: unknown[] }) => {
            seen.push(req.messages);
            return { choices: [{ message: { content: "Headline: x\nSummary: y." } }] };
          },
        },
      },
    } as unknown as ChatClient;

    const write = makeReleaseNoteWriter(opik, () => stub);
    const out = await write(loadChangeLists()[1]!, "v2");

    expect(out).toBe("Headline: x\nSummary: y.");
    expect(asked[0]).toMatchObject({ name: "release-note-headline", version: "v2" });
    expect(JSON.stringify(seen[0])).toContain("SYSTEM RULES");
    expect(JSON.stringify(seen[0])).toContain("tidepool doctor");
  });
});
