// `verify` subcommand: read the traces back from Opik's REST API and check the lesson —
// the tree has llm and tool spans, llm spans carry usage and cost, and the trace token
// total equals the sum of its llm spans (no double counting).
import { OPIK_PROJECT } from "./project.ts";

type Row = Record<string, any>;

async function get(path: string, params: Record<string, string>): Promise<Row> {
  const base = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
  const headers: Record<string, string> = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  const res = await fetch(`${base}/v1/private/${path}?${new URLSearchParams(params)}`, { headers });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status} ${await res.text()}`);
  return res.json() as Promise<Row>;
}

// `since` (ISO time) skips traces from earlier runs that are still in the project.
export async function verifyProject(since = ""): Promise<boolean> {
  const all = (await get("traces", { project_name: OPIK_PROJECT, size: "50" })).content as Row[];
  const traces = all.filter((t) => t.start_time >= since);
  console.log(`project ${OPIK_PROJECT}: ${traces.length} traces`);
  let ok = traces.length > 0;
  for (const t of traces.sort((a, b) => a.start_time.localeCompare(b.start_time))) {
    const spans = (await get("spans", { project_name: OPIK_PROJECT, trace_id: t.id, size: "500" })).content as Row[];
    const byType: Record<string, number> = {};
    for (const s of spans) byType[s.type] = (byType[s.type] ?? 0) + 1;
    const llm = spans.filter((s) => s.type === "llm" && s.usage?.total);
    const sumTokens = llm.reduce((n, s) => n + s.usage.total, 0);
    const priced = llm.filter((s) => s.total_estimated_cost > 0).length;
    const consistent = t.usage?.total === sumTokens;
    ok &&= llm.length > 0 && priced === llm.length && consistent && !!t.input && !!t.output;
    console.log(
      `${t.id}  spans=${spans.length} ${JSON.stringify(byType)}  iterations=${spans.filter((s) => /^iteration-/.test(s.name)).length}` +
        `\n   llm spans with usage=${llm.length} priced=${priced}  trace tokens=${t.usage?.total} sum(llm)=${sumTokens} ${consistent ? "OK" : "MISMATCH"}` +
        `\n   trace cost=${t.total_estimated_cost}  input=${JSON.stringify(t.input)?.slice(0, 60)}  output=${JSON.stringify(t.output)?.slice(0, 60)}`,
    );
  }
  console.log(ok ? "VERIFY OK" : "VERIFY FAILED");
  return ok;
}
