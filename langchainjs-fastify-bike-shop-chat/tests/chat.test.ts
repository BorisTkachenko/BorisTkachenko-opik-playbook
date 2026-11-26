import { describe, expect, it } from "vitest";
import { FakeListChatModel } from "@langchain/core/utils/testing";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

import { createChat, SessionStore } from "../src/chat.js";
import { buildServer } from "../src/server.js";
import { handlerFor } from "../src/tracing.js";

// Run these with OPIK_TRACK_DISABLE=true (see README): the Opik handler below is created and
// passed exactly like in production, but the SDK sends nothing anywhere.

const fake = (replies: string[]) => new FakeListChatModel({ responses: replies }) as unknown as BaseChatModel;

describe("chat chain", () => {
  it("returns the model's text and remembers the turn", async () => {
    const sessions = new SessionStore();
    const answer = createChat(fake(["It costs $59.", "Two days."]), sessions);
    expect(await answer("s1", "How much is a basic tune-up?")).toBe("It costs $59.");
    await answer("s1", "How long?");
    expect(sessions.get("s1").history).toHaveLength(4);
    expect(sessions.get("other").history).toHaveLength(0);
  });

  it("works with the Opik callback handler attached while tracking is disabled", async () => {
    const answer = createChat(fake(["Closed on Sundays."]), new SessionStore());
    const reply = await answer("s2", "Open Sunday?", { callbacks: [handlerFor("s2")] });
    expect(reply).toBe("Closed on Sundays.");
  });
});

describe("POST /chat", () => {
  it("rejects a body without a sessionId", async () => {
    const app = buildServer(fake(["x"]));
    const res = await app.inject({ method: "POST", url: "/chat", payload: { message: "hi" } });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("answers { reply, sessionId } for a valid body", async () => {
    const app = buildServer(fake(["Hello from the shop."]));
    const res = await app.inject({ method: "POST", url: "/chat", payload: { message: "hi", sessionId: "t" } });
    expect(res.json()).toEqual({ reply: "Hello from the shop.", sessionId: "t" });
    await app.close();
  });
});
