// The attribute rename that makes Opik understand VoltAgent's spans.
//
// VoltAgent names things `llm.usage.prompt_tokens`, `llm.model`, `span.type`...
// Opik's OTLP ingestion only recognises the OpenTelemetry GenAI conventions
// (`gen_ai.*`). Unmapped, every span arrives typed "general" with no model, no
// token usage and no cost. These copies are what make them llm / tool spans.
//
// Opik also files every attribute it does not recognise into the span INPUT, so after
// copying we delete VoltAgent's own bookkeeping; otherwise each input is a wall of ids.
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";

export type Attrs = Record<string, unknown>;

// VoltAgent bookkeeping that would otherwise be dumped into the span input. The root span's
// summed `usage.*` is dropped on purpose: re-mapping it to gen_ai.usage.* would type the
// agent span as llm and double-count the trace's tokens.
const NOISE = /^(operation\.|entity\.|voltagent\.|agent\.|span\.|llm\.|ai\.|usage\.|tool\.)/;

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
    if (attrs["llm.finish_reason"] !== undefined) attrs["gen_ai.response.finish_reasons"] = attrs["llm.finish_reason"];
  } else if (kind === "tool") {
    // VoltAgent records the tool-call arguments as a JSON string in its `input` attribute.
    // Opik reads tool input from gen_ai.tool.call.arguments, so mirror it there and drop
    // `input`, which Opik would otherwise merge into the span input a second time.
    attrs["gen_ai.tool.name"] = attrs["tool.name"];
    attrs["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
    delete attrs["input"];
  }
  // Agent root span (no span.type): its `input` / `output` attributes already map to the
  // span input / output, and the trace input / output come from this span.

  for (const k of Object.keys(attrs)) if (NOISE.test(k)) delete attrs[k];
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
