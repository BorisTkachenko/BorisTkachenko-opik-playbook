/**
 * Reads the project back from Opik's REST API and checks the lesson:
 * threads exist, every root run is plain text, retrieval shows up as a tool span.
 * Run after the demo:  npm run verify
 */
import { PROJECT_NAME } from "../src/tracing.js";

const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/$/, "");
const headers: Record<string, string> = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

async function get(pathAndQuery: string): Promise<any> {
  const r = await fetch(`${base}${pathAndQuery}`, { headers });
  if (!r.ok) throw new Error(`${pathAndQuery}: ${r.status} ${await r.text()}`);
  return r.json();
}

const q = `project_name=${encodeURIComponent(PROJECT_NAME)}`;
const traces = (await get(`/v1/private/traces?${q}&size=100`)).content as any[];
console.log(`traces: ${traces.length}`);

let bad = 0;
const threads = new Map<string, number>();
for (const t of traces) {
  threads.set(t.thread_id ?? "(none)", (threads.get(t.thread_id ?? "(none)") ?? 0) + 1);
  // For a string-in chain the handler stores { input: { value: "<text>" } } (and the
  // same under "output"): one key, one string. A message array or dict would break this shape.
  const isText = (x: any, key: string) =>
    x && Object.keys(x).length === 1 && typeof x[key]?.value === "string";
  const plain = isText(t.input, "input");
  const out = isText(t.output, "output");
  if (!plain || !out) {
    bad++;
    console.log("  NOT string-in/string-out:", t.id, JSON.stringify(t.input).slice(0, 80), JSON.stringify(t.output).slice(0, 80));
  }
}
console.log("threads:", Object.fromEntries(threads));

const spans = (await get(`/v1/private/spans?${q}&size=1000`)).content as any[];
const shape = new Map<string, number>();
for (const s of spans) shape.set(`${s.type}:${s.name}`, (shape.get(`${s.type}:${s.name}`) ?? 0) + 1);
console.log(`spans: ${spans.length}`, Object.fromEntries(shape));
const llm = spans.filter((s) => s.type === "llm");
console.log(
  "llm spans with usage:", llm.filter((s) => s.usage?.total_tokens).length, "/", llm.length,
  "| with cost:", llm.filter((s) => s.total_estimated_cost > 0).length
);
const sample = traces[traces.length - 1];
if (sample) console.log("sample root:", JSON.stringify(sample.input), "->", JSON.stringify(sample.output).slice(0, 100));

const tools = spans.filter((s) => s.type === "tool" && s.name === "lookup_shop_info").length;
if (bad || tools !== traces.length) {
  console.error(`FAIL: ${bad} non-text roots, ${tools} retrieval tool spans for ${traces.length} traces`);
  process.exit(1);
}
console.log("OK: every root is text and every turn has a lookup_shop_info tool span");
