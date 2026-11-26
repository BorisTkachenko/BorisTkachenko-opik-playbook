import { loadEnv } from "./lib/server/env";
import { setupOpik } from "./lib/telemetry";

loadEnv();
const flushOpik = setupOpik();

// On SIGTERM (what the demo sends), flush buffered spans to Opik before the process exits.
// Without this the last turn's trace can be lost, because the exporter batches.
process.once("SIGTERM", async () => {
  await flushOpik();
  process.exit(0);
});

