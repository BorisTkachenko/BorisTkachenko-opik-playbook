// Tracing is plain OpenTelemetry, so OTEL_SDK_DISABLED=true turns the exporter off.
// The BeeAI instrumentation stays patched in, and instrumented code runs unchanged.
import { describe, expect, it } from "vitest";

process.env.OTEL_SDK_DISABLED = "true";

describe("with tracing disabled", () => {
  it("runs an instrumented tool and shuts down cleanly", async () => {
    const { shutdownTracing } = await import("../src/telemetry/index.ts");
    const { trackCapacityTool } = await import("../src/tools/index.ts");
    const out = await trackCapacityTool.run({ track: "frontend" });
    expect(out.getTextContent()).toContain("Thu 13:00");
    await shutdownTracing();
  });
});
