// All of the Opik wiring lives here; nothing else in the app knows tracing exists.
//
// BeeAI is instrumented by OpenInference, which emits OpenTelemetry spans; an OTLP
// exporter sends them to Opik's OpenTelemetry endpoint. Workspace and project travel
// as plain HTTP headers, so no Opik SDK is involved.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { BeeAIInstrumentation } from "@arizeai/openinference-instrumentation-beeai";
import { OpikAttributeMapper } from "./mapper.ts";
import * as beeaiFramework from "beeai-framework";

import { OPIK_PROJECT } from "./project.ts";
export { OPIK_PROJECT };

const apiBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
const instrumentation = new BeeAIInstrumentation();

const headers: Record<string, string> = {
  // Selects the workspace the spans are written to.
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  // Selects the Opik project; without it the traces land in "Default Project".
  projectName: OPIK_PROJECT,
};
// Self-hosted Opik takes no key; Opik Cloud wants it in Authorization.
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

const sdk = new NodeSDK({
  // http/protobuf: the encoding Opik's OTLP endpoint is documented to take.
  // The mapper must come first: it rewrites each span's attributes before the batch
  // processor hands the span to the exporter.
  spanProcessors: [
    new OpikAttributeMapper(),
    new BatchSpanProcessor(new OTLPTraceExporter({ url: `${apiBase}/v1/private/otel/v1/traces`, headers })),
  ],
  // OpenInference patches BeeAI so every agent run, ReAct iteration, LLM call and tool
  // call becomes a span.
  instrumentations: [instrumentation],
});
sdk.start();

// tsx has already loaded beeai-framework by the time the module hook could see it, so
// patch the loaded module by hand (the instrumentation's documented fallback).
instrumentation.manuallyInstrument(beeaiFramework);

/** Flush the batch exporter; without it the last spans die with the process. */
export async function shutdownTracing(): Promise<void> {
  await sdk.shutdown();
}
