import { describe, expect, it } from "vitest";
import { buildRulePayload, ensureRule, RULE_NAME, SCORE_NAMES } from "../scripts/rule.mjs";

// A tiny in-memory Opik: just enough of the REST surface that ensureRule touches.
function fakeOpik(opts: { enabled?: boolean } = {}) {
  const state = { projects: [] as any[], rules: [] as any[], calls: [] as string[] };
  const call = async (method: string, path: string, body?: any) => {
    state.calls.push(`${method} ${path.split("?")[0]}`);
    if (path.startsWith("v1/private/projects") && method === "GET") return { content: state.projects };
    if (path.startsWith("v1/private/projects") && method === "POST") return void state.projects.push({ id: "p1", name: body.name });
    if (path.startsWith("v1/private/automations/evaluators") && method === "GET") return { content: state.rules };
    if (path.startsWith("v1/private/automations/evaluators") && method === "POST")
      return void state.rules.push({ id: "r1", name: body.name, enabled: opts.enabled ?? true });
    if (method === "PATCH") {
      state.rules[0].enabled = true;
      return null;
    }
    throw new Error(`unexpected ${method} ${path}`);
  };
  return { call, state };
}

describe("online evaluation rule", () => {
  it("maps trace input/output and declares the scores the judge returns", () => {
    const p = buildRulePayload("p1");
    expect(p.type).toBe("llm_as_judge");
    expect(p.enabled).toBe(true);
    expect(p.project_ids).toEqual(["p1"]);
    expect(p.code.schema.map((s: any) => s.name)).toEqual(SCORE_NAMES);
    // every {{placeholder}} in the prompt has a variable mapping
    const used = [...p.code.messages[0].content.matchAll(/{{(\w+)}}/g)].map((m) => m[1]);
    expect(used.sort()).toEqual(Object.keys(p.code.variables).sort());
  });

  it("creates the rule once and never duplicates it on a re-run", async () => {
    const { call, state } = fakeOpik();
    expect((await ensureRule(call)).created).toBe(true);
    expect((await ensureRule(call)).created).toBe(false);
    expect(state.rules.filter((r) => r.name === RULE_NAME)).toHaveLength(1);
    expect(state.calls.filter((c) => c === "POST v1/private/automations/evaluators")).toHaveLength(1);
  });

  it("re-enables an existing rule that was switched off", async () => {
    const { call, state } = fakeOpik({ enabled: false });
    await ensureRule(call); // creates (disabled in the fake)
    const again = await ensureRule(call);
    expect(again.created).toBe(false);
    expect(state.rules[0].enabled).toBe(true);
  });
});
