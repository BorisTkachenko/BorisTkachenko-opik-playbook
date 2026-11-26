import { defineConfig } from "vitest/config";

export default defineConfig({
  // OPIK_TRACK_DISABLE=true is the SDK's documented switch for turning tracing off: traced
  // functions still run, they just send nothing to Opik. Offline tests need it so they never
  // try to reach a server.
  test: { env: { OPIK_TRACK_DISABLE: "true" } },
});
