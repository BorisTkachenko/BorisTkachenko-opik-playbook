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

import { createChat, SessionStore } from "./chat.js";

const here = path.dirname(fileURLToPath(import.meta.url));

// Load the example's .env, then walk up to the repo-root .env (existing values win).
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

export function buildServer() {
  const sessions = new SessionStore();
  const answer = createChat(new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 }), sessions);

  const app = Fastify({ logger: false });
  app.register(fastifyStatic, { root: path.join(here, "../public") });

  app.post<{ Body: { message?: unknown; sessionId?: unknown } }>("/chat", async (req, reply) => {
    const { message, sessionId } = req.body ?? {};
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      return reply.code(400).send({ error: "Body must be { message: string, sessionId: string }" });
    }
    try {
      return { reply: await answer(sessionId, message), sessionId };
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
      process.exit(0);
    });
  }
}
