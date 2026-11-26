// Scripted demo: four guest conversations against the reservation agent, then
// exit. No server, no input. Run with `npm run demo`.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Example .env first, then the repo-root .env (the walk-up every example uses).
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});
delete process.env.OPENAI_BASE_URL;

// VoltAgent puts the system prompt in the messages array, which makes the AI SDK
// warn on every call. That layout is VoltAgent's, so drop that one known line.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { VoltAgent } = await import("@voltagent/core");
const { reservationAgent } = await import("./agent.ts");

// Registering the agent on a VoltAgent instance (no `server` option, so no HTTP port).
new VoltAgent({ agents: { reservationAgent } });

const GUESTS = [
  // Full at 19:00 on the 5th -> agent should offer alternatives.
  "Hi! Do you have a table for 4 on December 5th at 19:00?",
  // Chains availability -> booking.
  "Then please book 4 for Dec 5th at 21:00 under the name Alvarez.",
  // Dietary lookup, no booking.
  "One of our group is vegan and another is gluten-free. What mains can they eat?",
  // Cancel an existing booking.
  "Please cancel booking BK-1004, our plans changed.",
];

for (const [i, message] of GUESTS.entries()) {
  console.log(`\n=== Conversation ${i + 1} ===\nGuest:     ${message}`);
  const result = await reservationAgent.generateText(message);
  console.log(`Assistant: ${result.text}`);
}
process.exit(0);
