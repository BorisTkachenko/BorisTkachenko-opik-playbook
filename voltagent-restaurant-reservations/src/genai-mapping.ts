// The attribute rename that makes Opik understand VoltAgent's spans.
//
// VoltAgent names things `llm.usage.prompt_tokens`, `llm.model`, `span.type`...
// Opik's OTLP ingestion only recognises the OpenTelemetry GenAI conventions
// (`gen_ai.*`). Unmapped, every span arrives typed "general" with no model, no
// token usage and no cost. These copies are what make them llm / tool spans.
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";

export type Attrs = Record<string, unknown>;

export function mapToGenAI(attrs: Attrs, provider = "openai"): Attrs {
  const kind = attrs["span.type"];
  if (kind === "llm") {
    // Model + provider: Opik prices a span only when it can resolve BOTH, via
    // gen_ai.request.model and gen_ai.system / gen_ai.provider.name.
    if (attrs["llm.model"]) attrs["gen_ai.request.model"] = attrs["llm.model"];
    attrs["gen_ai.system"] = provider; // also what types the span as `llm`
    attrs["gen_ai.provider.name"] = provider;
    // Token usage: becomes span.usage and the trace-level token totals.
    for (const key of ["prompt_tokens", "completion_tokens", "total_tokens"]) {
      const value = attrs[`llm.usage.${key}`];
      if (value !== undefined) attrs[`gen_ai.usage.${key}`] = value;
    }
    // The chat messages become the span input.
    if (attrs["llm.messages"] !== undefined) attrs["gen_ai.prompt"] = attrs["llm.messages"];
  } else if (kind === "tool") {
    // VoltAgent records the tool-call arguments as a JSON string in its `input` attribute.
    // Opik reads tool input from gen_ai.tool.call.arguments, so mirror it there.
    attrs["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
  }
  return attrs;
}

// Wraps the OTLP exporter and renames VoltAgent's attributes just before they are
// serialised. OPIK_GENAI_MAPPING=off skips it, to reproduce the "before" traces.
export class GenAIMappingExporter implements SpanExporter {
  constructor(private readonly inner: SpanExporter) {}
  export(spans: ReadableSpan[], done: Parameters<SpanExporter["export"]>[1]): void {
    if (process.env.OPIK_GENAI_MAPPING !== "off") for (const s of spans) mapToGenAI(s.attributes as Attrs);
    this.inner.export(spans, done);
  }
  shutdown = () => this.inner.shutdown();
  forceFlush = () => this.inner.forceFlush?.() ?? Promise.resolve();
}
