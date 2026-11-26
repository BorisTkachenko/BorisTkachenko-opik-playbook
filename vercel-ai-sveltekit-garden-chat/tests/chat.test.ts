import { describe, expect, it } from "vitest";
import { MockLanguageModelV4, simulateReadableStream } from "ai/test";
import type { UIMessage } from "ai";
import { lastQuestion, startChat } from "../src/lib/server/chat";
import { enrichFromContext } from "../src/lib/telemetry";

const user = (text: string): UIMessage => ({ id: "m1", role: "user", parts: [{ type: "text", text }] });

describe("chat turn", () => {
  it("reads the last user message as the question", () => {
    expect(lastQuestion([user("first"), { id: "a", role: "assistant", parts: [{ type: "text", text: "x" }] }, user("second")])).toBe("second");
  });

  // The Opik hook (OpikExporter.getSettings + runtimeContext) must not get in the way of a normal
  // call. Tracking is switched off by OPIK_TRACK_DISABLE=true and no telemetry integration is
  // registered here, so this runs offline with no Opik server and no API key.
  it("streams an answer through the Opik-instrumented call with tracking disabled", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    const model = new MockLanguageModelV4({
      doStream: async () => ({
        stream: simulateReadableStream({
          chunks: [
            { type: "text-start", id: "t" },
            { type: "text-delta", id: "t", delta: "Plant after 12 May." },
            { type: "text-end", id: "t" },
            {
              type: "finish",
              finishReason: { unified: "stop", raw: "stop" },
              usage: {
                inputTokens: { total: 10, noCache: 10, cacheRead: undefined, cacheWrite: undefined },
                outputTokens: { total: 5, text: 5, reasoning: undefined },
              },
            },
          ],
        }),
      }),
    } as any);
    const result = await startChat(model, "chat-1", [user("When do I plant tomatoes?")]);
    expect(await result.text).toBe("Plant after 12 May.");
    // retrieval ran: the warm-season excerpt reached the model's system prompt
    expect(JSON.stringify(model.doStreamCalls[0].prompt)).toContain("after the last frost on 12 May");
  });

  it("copies the chat id and trace name onto span attributes for Opik", () => {
    expect(enrichFromContext({ threadId: "abc", traceName: "garden-chat-turn" })).toEqual({
      "ai.telemetry.metadata.threadId": "abc",
      "ai.telemetry.metadata.traceName": "garden-chat-turn",
    });
    expect(enrichFromContext(undefined)).toEqual({});
  });
});
