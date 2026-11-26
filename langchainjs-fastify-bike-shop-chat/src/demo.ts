/**
 * Scripted demo: boot the Fastify server on a spare port, play three
 * multi-turn visitor conversations over HTTP, print the replies, shut down.
 */
import { buildServer } from "./server.js";
import { flushOpik, PROJECT_NAME } from "./tracing.js";

const PORT = Number(process.env.PORT ?? 5451);

export const CONVERSATIONS: Record<string, string[]> = {
  "visitor-tuneup-booking": [
    "Hi! My commuter bike is making grinding noises. What tune-ups do you offer?",
    "How much is the full one, and how long will it take?",
    "Great. What slots are open on Thursday or Saturday?",
  ],
  "visitor-opening-hours": [
    "Are you open on Sundays?",
    "Okay, what about Thursday evening?",
  ],
  "visitor-flat-tyre": [
    "I got a flat on my way to work, can you fix it while I wait?",
    "Does the 15 dollars include a new tube?",
    "Can you also repair my carbon fork?",
  ],
};

async function chat(sessionId: string, message: string): Promise<string> {
  const response = await fetch(`http://127.0.0.1:${PORT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!response.ok) throw new Error(`POST /chat failed: ${response.status} ${await response.text()}`);
  return ((await response.json()) as { reply: string }).reply;
}

async function main() {
  const app = buildServer();
  await app.listen({ port: PORT, host: "127.0.0.1" });
  console.log(`Demo server up on http://127.0.0.1:${PORT}`);

  for (const [sessionId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== ${sessionId} ===`);
    for (const message of turns) {
      console.log(`\nVisitor: ${message}`);
      console.log(`Bot:     ${await chat(sessionId, message)}`);
    }
  }

  await app.close();
  // The server is down, but the SDK still holds batched traces: flush before the process exits.
  await flushOpik();
  console.log(`\nDone. Open the "${PROJECT_NAME}" project in Opik and look at the Threads tab.`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
