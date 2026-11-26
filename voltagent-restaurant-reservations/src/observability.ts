// VoltAgent observability wired to Opik. VoltAgent's tracing is plain
// OpenTelemetry underneath, so an OTLP exporter aimed at Opik's OTel endpoint
// is the whole integration. This is the only file that knows tracing exists.
import { VoltAgentObservability } from "@voltagent/core";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { GenAIMappingExporter } from "./genai-mapping.ts";

export const PROJECT = process.env.OPIK_PROJECT_NAME ?? "voltagent-restaurant-reservations";

// OPIK_URL_OVERRIDE is the REST base (e.g. http://localhost:5173/api/); Opik's
// OTLP ingestion lives under it at /v1/private/otel.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");

// Self-hosted Opik must NOT get an Authorization header; Opik Cloud needs one.
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default", // which workspace receives the spans
  projectName: PROJECT, // which Opik project; without it traces land in "Default Project"
};
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

export const observability = new VoltAgentObservability({
  serviceName: PROJECT,
  spanProcessors: [
    // http/protobuf is the OTLP transport verified against Opik's endpoint.
    // The wrapper renames VoltAgent's attributes to gen_ai.* so llm spans carry model, usage and cost.
    new BatchSpanProcessor(
      new GenAIMappingExporter(new OTLPTraceExporter({ url: `${opikBase}/v1/private/otel/v1/traces`, headers })),
    ),
  ],
});
