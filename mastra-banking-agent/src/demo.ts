// Plays four scripted customer requests against the banking agent. Each one
// becomes one trace in the Opik project "mastra-banking-agent".
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Example .env first, then the repo-root .env (dotenv never overrides set vars).
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});
if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Import Mastra only after env vars are loaded: the exporter reads them at module init.
const { mastra } = await import("./mastra.ts");

const REQUESTS = [
  // 1. One tool call.
  "What's my checking balance?",
  // 2. One tool call with filters the model must translate from prose.
  "Show me my last three dining or shopping purchases over $5 on checking, and tell me the biggest.",
  // 3. Chain: balance + transactions on two accounts.
  "How much do I have across checking and savings, and what's the most recent thing that hit savings?",
  // 4. A state change, then a follow-up read of the effect.
  "I lost my Visa ending 4417. Freeze it right away and confirm.",
];

const agent = mastra.getAgent("bankingAgent");
for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===\nCustomer: ${request}`);
  const result = await agent.generate(request, { maxSteps: 6 });
  console.log(`Agent:    ${result.text}`);
}

// shutdown() flushes the OTel exporter; without it the last spans may never reach Opik.
await mastra.shutdown();
console.log('\nDone. Open the "mastra-banking-agent" project in Opik.');
