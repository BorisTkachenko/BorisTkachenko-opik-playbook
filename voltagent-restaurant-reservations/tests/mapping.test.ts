import { describe, expect, it } from "vitest";
import type { ReadableSpan } from "@opentelemetry/sdk-trace-base";
import { GenAIMappingExporter, mapToGenAI } from "../src/genai-mapping.ts";

// Attribute bags shaped like the ones VoltAgent really emits (captured from a run).
const llm = () => ({
  "span.type": "llm",
  "llm.model": "gpt-4o-mini",
  "llm.usage.prompt_tokens": 622,
  "llm.usage.completion_tokens": 41,
  "llm.usage.total_tokens": 663,
  "llm.messages": '[{"role":"user","content":"hi"}]',
});

describe("mapToGenAI", () => {
  it("copies model, provider and token usage to gen_ai.* on llm spans", () => {
    const a = mapToGenAI(llm());
    expect(a["gen_ai.request.model"]).toBe("gpt-4o-mini");
    expect(a["gen_ai.system"]).toBe("openai");
    expect(a["gen_ai.provider.name"]).toBe("openai");
    expect(a["gen_ai.usage.prompt_tokens"]).toBe(622);
    expect(a["gen_ai.usage.completion_tokens"]).toBe(41);
    expect(a["gen_ai.usage.total_tokens"]).toBe(663);
  });

  it("drops VoltAgent bookkeeping so span input is not a wall of ids", () => {
    const a = mapToGenAI({ ...llm(), "operation.id": "x", "entity.id": "agent", "usage.prompt_context.total_tokens_estimated": 459 });
    expect(Object.keys(a).filter((k) => !k.startsWith("gen_ai."))).toEqual([]);
  });

  it("mirrors tool arguments to gen_ai.tool.call.arguments and drops the raw input", () => {
    const a = mapToGenAI({ "span.type": "tool", "tool.name": "list_dietary_menu", input: '{"diet":"vegan"}' });
    expect(a["gen_ai.tool.call.arguments"]).toBe('{"diet":"vegan"}');
    expect(a).not.toHaveProperty("input");
  });

  it("never types the agent root span as llm, so trace tokens are not double-counted", () => {
    const a = mapToGenAI({ "entity.type": "agent", input: "hi", output: "hello", "usage.total_tokens": 663 });
    expect(a).toEqual({ input: "hi", output: "hello" });
  });
});

describe("GenAIMappingExporter", () => {
  const run = (attrs: Record<string, unknown>) => {
    let seen: ReadableSpan[] = [];
    const inner = { export: (s: ReadableSpan[], cb: any) => ((seen = s), cb({ code: 0 })), shutdown: async () => {}, forceFlush: async () => {} };
    new GenAIMappingExporter(inner as any).export([{ attributes: attrs } as ReadableSpan], () => {});
    return seen[0].attributes;
  };

  it("maps before handing spans to the inner exporter", () => {
    expect(run(llm())["gen_ai.usage.total_tokens"]).toBe(663);
  });

  it("can be switched off to reproduce the unmapped traces", () => {
    process.env.OPIK_GENAI_MAPPING = "off";
    try {
      expect(run(llm())["gen_ai.usage.total_tokens"]).toBeUndefined();
    } finally {
      delete process.env.OPIK_GENAI_MAPPING;
    }
  });
});
