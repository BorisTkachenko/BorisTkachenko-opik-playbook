import { NodeSDK } from "@opentelemetry/sdk-node";
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";

export const PROJECT_NAME = "vercel-ai-sveltekit-garden-chat";

// Turn the runtimeContext the route passes into the span attributes Opik reads.
// Pure function so tests can check the mapping without any OpenTelemetry setup.
export function enrichFromContext(runtimeContext?: Record<string, unknown>): Record<string, string> {
  const attributes: Record<string, string> = {};
  if (runtimeContext?.threadId != null) attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
  if (runtimeContext?.traceName != null) attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
  return attributes;
}

let sdk: NodeSDK | undefined;

// Called once from hooks.server.ts. Returns a shutdown function that flushes pending traces.
export function setupOpik(): () => Promise<void> {
  if (sdk) return () => sdk!.shutdown();

  // OpikExporter is an OpenTelemetry span exporter: it turns the AI SDK's spans into Opik
  // traces + llm spans (usage and cost included). projectName pins every trace to this
  // example's project; without it traces land in "Default Project".
  sdk = new NodeSDK({
    serviceName: PROJECT_NAME,
    traceExporter: new OpikExporter({
      client: new Opik({ projectName: PROJECT_NAME }),
      tags: ["sveltekit", "streaming"],
    }),
  });
  sdk.start();

  // AI SDK v7 emits NO telemetry until an integration is registered. Without this call the
  // project stays empty. enrichSpan copies the thread id onto each span; Opik groups traces
  // that share it into one thread.
  registerTelemetry(
    new OpenTelemetry({
      usage: true,
      enrichSpan: ({ runtimeContext }) => enrichFromContext(runtimeContext as Record<string, unknown> | undefined),
    }),
  );

  return () => sdk!.shutdown(); // shutdown() force-flushes the batch exporter
}
