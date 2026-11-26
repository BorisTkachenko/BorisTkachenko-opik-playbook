// Entry point: `triage <id>` runs one proposal, `demo` runs three, `list` shows the pile.
import { parseArgs } from "node:util";
import { loadEnv, requireKey } from "./config/env.ts";

const DEMO_IDS = ["P-1001", "P-1005", "P-1003"];

async function main(): Promise<void> {
  const { positionals } = parseArgs({ allowPositionals: true });
  const [command, arg] = positionals;
  loadEnv();

  if (command === "list") {
    const { proposals } = await import("./data/store.ts");
    for (const p of proposals()) console.log(`${p.id}  [${p.track}]  ${p.title}`);
    return;
  }
  if (command !== "triage" && command !== "demo") {
    console.error("Usage: cli.ts <list | triage <proposal-id> | demo>");
    process.exit(2);
  }
  requireKey("OPENAI_API_KEY");

  // Start tracing before BeeAI is imported so the instrumentation can patch it.
  const { shutdownTracing, OPIK_PROJECT } = await import("./telemetry/index.ts");
  const { triageProposal } = await import("./agent/triage.ts");
  const ids = command === "demo" ? DEMO_IDS : [arg ?? ""];
  for (const id of ids) {
    console.log(`\n=== ${id} ===`);
    console.log(await triageProposal(id));
  }
  // Flush so the final spans reach Opik before the process exits.
  await shutdownTracing();
  console.log(`\nDone. Open the "${OPIK_PROJECT}" project in Opik to see the traces.`);
}

await main();
