/**
 * Read the project back from Opik's REST API and check the lesson holds: each
 * episode is ONE trace whose spans come from two OS processes, with the failed
 * upload attempts (errorInfo) followed by the successful one. Exits non-zero if not.
 * Run with `npm run verify` after `npm run demo`.
 */
import './env';

const base = (process.env.OPIK_URL_OVERRIDE ?? 'https://www.comet.com/opik/api/').replace(/\/$/, '');
const project = process.env.OPIK_PROJECT_NAME!;
const headers: Record<string, string> = { 'Comet-Workspace': process.env.OPIK_WORKSPACE ?? 'default' };
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

/* eslint-disable @typescript-eslint/no-explicit-any */
async function get(pathAndQuery: string): Promise<any> {
  const res = await fetch(`${base}${pathAndQuery}`, { headers });
  if (!res.ok) throw new Error(`GET ${pathAndQuery} -> ${res.status}`);
  return res.json();
}

async function main() {
  const q = `project_name=${encodeURIComponent(project)}`;
  const { content: traces } = await get(`/v1/private/traces?${q}&size=50`);
  console.log(`project "${project}": ${traces.length} trace(s)`);
  let failures = 0;
  const check = (ok: boolean, msg: string) => {
    console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${msg}`);
    if (!ok) failures++;
  };
  check(traces.length >= 1, 'project has traces');
  for (const t of traces.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time))) {
    const { content: spans } = await get(`/v1/private/spans?${q}&trace_id=${t.id}&size=100`);
    spans.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));
    console.log(`\ntrace ${t.name}  (${t.id})  spans=${spans.length}  total_cost=$${t.total_estimated_cost}`);
    const pids = new Set<number>(
      [t.metadata?.process?.pid, ...spans.map((s: any) => s.metadata?.process?.pid)].filter(Boolean),
    );
    // Print as a tree: children right under their parent, in start order.
    const print = (parentId: string | null, indent: number) => {
      for (const s of spans.filter((x: any) => (x.parent_span_id ?? null) === parentId)) {
        const err = s.error_info ? `  ERROR: ${s.error_info.message}` : '';
        const tok = s.usage?.total_tokens ? `  tokens=${s.usage.total_tokens} cost=${s.total_estimated_cost}` : '';
        console.log(`  ${'  '.repeat(indent)}${s.name} [${s.type}]${tok}${err}`);
        print(s.id, indent + 1);
      }
    };
    print(null, 0);
    const uploads = spans.filter((s: any) => s.name.startsWith('uploadToCdn'));
    const failed = uploads.filter((s: any) => s.error_info);
    check(pids.size === 2, `spans come from 2 OS processes (pids ${[...pids].join(', ')})`);
    check(spans.every((s: any) => s.trace_id === t.id), 'every span belongs to this one trace');
    check(failed.length >= 1 && uploads.length === failed.length + 1, `uploadToCdn: ${failed.length} failed attempt(s), then 1 success`);
    check(!uploads[uploads.length - 1]?.error_info, 'the last upload attempt carries no error');
    const llm = spans.filter((s: any) => s.usage?.total_tokens);
    check(llm.length === 2 && llm.every((s: any) => s.total_estimated_cost > 0), 'both LLM spans have token usage and a cost');
    const attempts = (t.feedback_scores ?? []).find((f: any) => f.name === 'cdn_upload_attempts');
    check(attempts?.value === uploads.length, `feedback score cdn_upload_attempts = ${attempts?.value} matches ${uploads.length} upload spans`);
    check(t.input != null && t.output != null, "trace keeps the starter's input and output");
  }
  if (failures) process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
