// Reads the project back from Opik and waits for the online rule's scores to land on this run's traces.
// Scores are written asynchronously by the Opik backend (a judge LLM call per trace), so we poll.
import { PROJECT_NAME, SCORE_NAMES, TRACE_NAME } from "./rule.mjs";

export async function collectRun(call, sinceIso) {
  const page = await call("GET", `v1/private/traces?project_name=${encodeURIComponent(PROJECT_NAME)}&size=100&truncate=false`);
  return (page.content ?? []).filter((t) => t.name === TRACE_NAME && t.start_time >= sinceIso);
}

export function summarize(traces) {
  const scored = traces.filter((t) => SCORE_NAMES.every((n) => t.feedback_scores?.some((s) => s.name === n)));
  return { total: traces.length, scored: scored.length };
}

// Polls until every trace carries every judge score, or the timeout passes. Returns the final traces.
export async function waitForScores(call, sinceIso, expected, { timeoutMs = 240_000, everyMs = 5_000, log = console.log } = {}) {
  const deadline = Date.now() + timeoutMs;
  let traces = [];
  for (;;) {
    traces = await collectRun(call, sinceIso);
    const { total, scored } = summarize(traces);
    log(`  traces ${total}/${expected}, fully scored ${scored}/${expected}`);
    if (total >= expected && scored >= expected) return traces;
    if (Date.now() > deadline) return traces;
    await new Promise((r) => setTimeout(r, everyMs));
  }
}

export async function report(call, traces) {
  const lines = [];
  for (const t of traces.sort((a, b) => a.start_time.localeCompare(b.start_time))) {
    const scores = Object.fromEntries((t.feedback_scores ?? []).map((s) => [s.name, s.value]));
    const spans = await call("GET", `v1/private/spans?trace_id=${t.id}&project_name=${encodeURIComponent(PROJECT_NAME)}&size=50`);
    const llm = (spans.content ?? []).filter((s) => s.type === "llm");
    const cost = llm.reduce((a, s) => a + (s.total_estimated_cost ?? 0), 0);
    lines.push({
      trace: t.id.slice(-8),
      name: t.name,
      thread: (t.thread_id ?? "-").slice(0, 8),
      spans: (spans.content ?? []).map((s) => `${s.type}:${s.name}`).join(","),
      tokens: t.usage?.total_tokens ?? llm.reduce((a, s) => a + (s.usage?.total_tokens ?? 0), 0),
      cost: cost.toFixed(6),
      scores,
    });
  }
  return lines;
}
