/**
 * Crankshaft Cycles chat widget backend: Fastify + LangChain.js.
 * POST /chat { message, sessionId } -> { reply, sessionId }.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";
import Fastify from "fastify";
import fastifyStatic from "@fastify/static";
import { ChatOpenAI } from "@langchain/openai";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

import { createChat, SessionStore } from "./chat.js";
import { flushOpik, handlerFor } from "./tracing.js";

const here = path.dirname(fileURLToPath(import.meta.url));

// Load the example's .env, then walk up to the repo-root .env (existing values win).
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

// The model is injectable so tests can pass a fake; the default needs OPENAI_API_KEY.
export function buildServer(model: BaseChatModel = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 })) {
  const sessions = new SessionStore();
  const answer = createChat(model, sessions);

  const app = Fastify({ logger: false });
  app.register(fastifyStatic, { root: path.join(here, "../public") });

  app.post<{ Body: { message?: unknown; sessionId?: unknown } }>("/chat", async (req, reply) => {
    const { message, sessionId } = req.body ?? {};
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      return reply.code(400).send({ error: "Body must be { message: string, sessionId: string }" });
    }
    try {
      // The per-session handler is passed as a LangChain callback: this one line is what
      // makes the turn show up in Opik (trace named bike-shop-turn, in this session's thread).
      const text = await answer(sessionId, message, { callbacks: [handlerFor(sessionId)] });
      return { reply: text, sessionId };
    } catch (error) {
      console.error("Chat turn failed:", error);
      return reply.code(500).send({ error: "The assistant could not answer. Please try again." });
    }
  });

  return app;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const port = Number(process.env.PORT ?? 3000);
  const app = buildServer();
  await app.listen({ port, host: "127.0.0.1" });
  console.log(`Crankshaft Cycles chat widget: http://localhost:${port}`);
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.on(signal, async () => {
      await app.close();
      await flushOpik(); // do not lose the last turns on Ctrl+C
      process.exit(0);
    });
  }
}
