// Creates (once) the live online-evaluation rule that scores every incoming trace.
// Plain REST on purpose: the rule is project configuration, not app code, and this keeps the setup
// visible in one file. Idempotent: the rule is looked up by name before creating.

export const PROJECT_NAME = "vercel-ai-sveltekit-garden-chat";
export const RULE_NAME = "garden_answer_quality";
export const TRACE_NAME = "garden-chat-turn"; // the chat traces; Opik also logs the judge's own calls as "online_evaluation" traces

// The two scores the judge returns. They appear in the trace's Feedback scores column under these names.
export const SCORE_NAMES = ["answer_relevance", "stays_in_guide"];

export function buildRulePayload(projectId) {
  return {
    type: "llm_as_judge",
    name: RULE_NAME,
    action: "evaluator",
    project_ids: [projectId],
    enabled: true,
    // 1.0 = judge every production trace. Fine for a demo; lower it (e.g. 0.1) for real traffic cost.
    sampling_rate: 1.0,
    code: {
      // The judge runs inside the Opik server and uses the OpenAI key stored under Settings > AI Providers.
      model: { name: "gpt-4o-mini", temperature: 0 },
      messages: [
        {
          role: "USER",
          content:
            "You grade a gardening assistant. It may only answer from a small local garden guide, " +
            "and must say so when the guide does not cover a question.\n\n" +
            "Conversation so far (the last user message is the question being answered):\n{{conversation}}\n\n" +
            "Assistant reply:\n{{reply}}\n\n" +
            "answer_relevance: true if the reply directly addresses the last user question.\n" +
            "stays_in_guide: true if the reply sticks to practical garden advice and does not invent " +
            "brands, products or facts that sound made up; an honest 'the guide does not cover this' also counts as true.",
        },
      ],
      // Variable mapping: {{conversation}} <- the whole trace input, {{reply}} <- the whole trace output.
      variables: { conversation: "input", reply: "output" },
      schema: [
        { name: "answer_relevance", type: "BOOLEAN", description: "Reply addresses the last user question" },
        { name: "stays_in_guide", type: "BOOLEAN", description: "Reply avoids made-up products or facts" },
      ],
    },
  };
}

export function opikClient(env = process.env, fetchImpl = fetch) {
  const base = (env.OPIK_URL_OVERRIDE || "http://localhost:5173/api/").replace(/\/?$/, "/");
  const headers = { "Content-Type": "application/json", "Comet-Workspace": env.OPIK_WORKSPACE || "default" };
  if (env.OPIK_API_KEY) headers.Authorization = env.OPIK_API_KEY;
  return async (method, path, body) => {
    const res = await fetchImpl(base + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    if (!res.ok) throw new Error(`${method} ${path} -> HTTP ${res.status}: ${await res.text()}`);
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  };
}

export async function ensureProject(call, name = PROJECT_NAME) {
  const found = await call("GET", `v1/private/projects?name=${encodeURIComponent(name)}&size=50`);
  const hit = found?.content?.find((p) => p.name === name);
  if (hit) return hit.id;
  // Creating the project up front lets the rule attach to it before the first trace exists.
  await call("POST", "v1/private/projects", { name });
  const again = await call("GET", `v1/private/projects?name=${encodeURIComponent(name)}&size=50`);
  return again.content.find((p) => p.name === name).id;
}

// Returns { id, created }. Never creates a second rule with the same name.
export async function ensureRule(call) {
  const projectId = await ensureProject(call);
  const list = await call(
    "GET",
    `v1/private/automations/evaluators?project_id=${projectId}&name=${encodeURIComponent(RULE_NAME)}&size=50`,
  );
  const existing = list?.content?.find((r) => r.name === RULE_NAME);
  if (existing) {
    if (!existing.enabled) {
      await call("PATCH", `v1/private/automations/evaluators/${existing.id}`, buildRulePayload(projectId));
    }
    return { id: existing.id, created: false };
  }
  await call("POST", "v1/private/automations/evaluators", buildRulePayload(projectId));
  const after = await call(
    "GET",
    `v1/private/automations/evaluators?project_id=${projectId}&name=${encodeURIComponent(RULE_NAME)}&size=50`,
  );
  return { id: after.content.find((r) => r.name === RULE_NAME).id, created: true };
}
