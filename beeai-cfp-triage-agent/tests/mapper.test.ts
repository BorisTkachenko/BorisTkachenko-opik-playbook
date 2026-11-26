import { describe, expect, it } from "vitest";
import { OpikAttributeMapper } from "../src/telemetry/mapper.ts";

const base = { traceId: "run1", name: "x" };

describe("OpikAttributeMapper", () => {
  it("joins model (start span) and provider onto the usage span", () => {
    const m = new OpikAttributeMapper();
    m.map({ ...base, "openinference.span.kind": "LLM", target: "backend.openai.chat.start", "llm.model_name": "gpt-4o-mini" });
    const success: Record<string, unknown> = {
      ...base,
      "openinference.span.kind": "LLM",
      target: "backend.openai.chat.success",
      "llm.token_count.total": 10,
      "llm.output_messages.0.message.content": "Thought",
    };
    m.map(success);
    expect(success["llm.model_name"]).toBe("gpt-4o-mini");
    expect(success["gen_ai.system"]).toBe("openai");
    expect(success["llm.output_messages.0.message.content"]).toBeUndefined();
  });

  it("turns tool parameters and result into the tool-call attributes", () => {
    const a: Record<string, unknown> = {
      ...base,
      "openinference.span.kind": "TOOL",
      "tool.parameters": '{"track":"ml"}',
      "output.value": '{"result":1}',
    };
    new OpikAttributeMapper().map(a);
    expect(a["gen_ai.tool.call.arguments"]).toBe('{"track":"ml"}');
    expect(a["gen_ai.tool.call.result"]).toBe('{"result":1}');
    expect(a["output.value"]).toBeUndefined();
  });

  it("unwraps the root output and moves bookkeeping into metadata", () => {
    const a: Record<string, unknown> = {
      ...base,
      source: "ReActAgent",
      "openinference.span.kind": "AGENT",
      "input.value": "prompt",
      "output.value": JSON.stringify({ role: "assistant", text: " Recommendation: accept " }),
      history: "[]",
    };
    new OpikAttributeMapper().map(a);
    expect(a["output.value"]).toBe("Recommendation: accept");
    expect(a["input.value"]).toBe("prompt");
    expect(a.history).toBeUndefined();
    expect(a.traceId).toBeUndefined();
    expect(a["opik.metadata.traceId"]).toBe("run1");
  });
});
