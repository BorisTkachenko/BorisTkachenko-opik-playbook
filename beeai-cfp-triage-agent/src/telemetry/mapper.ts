// Rewrites OpenInference attributes into the names Opik's OTLP ingestion understands.
// Lives in its own file so it can be unit-tested without an exporter.
import type { Context } from "@opentelemetry/api";
import type { ReadableSpan, Span, SpanProcessor } from "@opentelemetry/sdk-trace-base";

type Attrs = Record<string, unknown>;

// Attribute prefixes Opik maps to something useful (input, output, model, usage, tool
// call, provider, metadata). Everything else gets moved into metadata.
const KEEP = ["input.", "output.", "llm.model_name", "llm.token_count.", "llm.invocation_parameters", "gen_ai.", "opik."];

export class OpikAttributeMapper implements SpanProcessor {
  // The LLM "success" span carries token counts but not the model name; the "start" span
  // carries the name. Remember it per BeeAI run so the pair can be joined.
  private modelByRun = new Map<string, string>();

  onStart(_span: Span, _ctx: Context): void {}

  onEnd(span: ReadableSpan): void {
    this.map(span.attributes as Attrs);
  }

  map(a: Attrs): void {
    const kind = a["openinference.span.kind"];
    const run = String(a.traceId ?? "");

    if (kind === "LLM") {
      if (typeof a["llm.model_name"] === "string") this.modelByRun.set(run, a["llm.model_name"]);
      // Opik prices a span only when model, provider and usage sit on the SAME span.
      // OpenInference splits them across start and success, so copy them across and add
      // gen_ai.system, the attribute Opik reads as the provider.
      if (typeof a["llm.token_count.total"] === "number") {
        a["llm.model_name"] ??= this.modelByRun.get(run);
        a["gen_ai.system"] = String(a.target ?? "").split(".")[1] ?? "openai";
      }
    }

    if (kind === "TOOL") {
      // gen_ai.tool.call.* are the attributes Opik turns into a `tool` span with input/output
      // (without them the span is typed `general`).
      if (a["tool.parameters"] !== undefined) a["gen_ai.tool.call.arguments"] = a["tool.parameters"];
      if (a["output.value"] !== undefined) a["gen_ai.tool.call.result"] = a["output.value"];
      delete a["output.value"];
    }

    if (kind === "AGENT" && a.source === "ReActAgent") {
      // Trace output = the root span's output. Unwrap BeeAI's message JSON to plain text.
      try {
        const parsed = JSON.parse(String(a["output.value"]));
        if (typeof parsed.text === "string") a["output.value"] = parsed.text.trim();
      } catch {
        /* leave as is */
      }
    }

    for (const key of Object.keys(a)) {
      // llm.*_messages.N.* repeat the streamed output one token at a time (about 130
      // attributes per call); input.value / output.value already hold the content.
      if (/^llm\.(input|output)_messages\./.test(key) || key === "history") delete a[key];
      else if (!KEEP.some((p) => key.startsWith(p))) {
        // Anything Opik has no rule for would be dumped into the span INPUT.
        // opik.metadata.* sends it to span metadata instead.
        a[`opik.metadata.${key}`] = a[key];
        delete a[key];
      }
    }
  }

  async forceFlush(): Promise<void> {}
  async shutdown(): Promise<void> {}
}
