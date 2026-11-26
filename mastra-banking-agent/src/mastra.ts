// Mastra instance wired to Opik through Mastra's OTel exporter. The agent and
// tool files contain no tracing code: this config is the whole integration.
import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { PinoLogger } from "@mastra/loggers";
import { LibSQLStore } from "@mastra/libsql";
import { bankingAgent } from "./agent.ts";

const PROJECT = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";

// OPIK_URL_OVERRIDE is the REST base (e.g. http://localhost:5173/api/); Opik's
// OTLP ingestion lives under it at /v1/private/otel.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");

// Opik Cloud needs Authorization; self-hosted local Opik must NOT get that header.
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default", // which workspace receives the spans
  projectName: PROJECT, // which Opik project; without it traces land in "Default Project"
};
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

export const mastra = new Mastra({
  agents: { bankingAgent },
  storage: new LibSQLStore({ id: "memory-store", url: ":memory:" }),
  logger: new PinoLogger({ name: "Mastra", level: "warn" }),
  observability: new Observability({
    configs: {
      default: {
        serviceName: PROJECT,
        exporters: [
          // OtelExporter turns Mastra's agent/LLM/tool spans into OTLP spans with
          // gen_ai.* attributes; Opik maps them to a trace tree (llm and tool spans).
          new OtelExporter({
            provider: { custom: { endpoint: `${opikBase}/v1/private/otel/v1/traces`, protocol: "http/protobuf", headers } },
          }),
        ],
      },
    },
  }),
});
