import { PROJECT_NAME, SUITE_NAME } from "./config.js"; // sets OPIK_PROJECT_NAME first
import { Opik } from "opik";
import { PROMPT_NAME } from "./prompts.js";

/** Read back what the demo wrote to Opik: traces, spans, cost, prompt versions and both suite runs. */
async function main(): Promise<void> {
  const opik = new Opik({ projectName: PROJECT_NAME });

  // Optional: pass an ISO timestamp to ignore anything older (e.g. earlier practice runs).
  const since = process.argv[2] ? new Date(process.argv[2]) : new Date(0);
  const traces = (await opik.searchTraces({ projectName: PROJECT_NAME, maxResults: 1000 })).filter((t) => t.startTime >= since);
  const spans = (await opik.searchSpans({ projectName: PROJECT_NAME, maxResults: 5000 })).filter((s) => s.startTime >= since);
  const byType: Record<string, number> = {};
  for (const s of spans) byType[s.type ?? "?"] = (byType[s.type ?? "?"] ?? 0) + 1;
  // Writer calls (opik-openai) and judge calls (the SDK's LLM judges) are the two kinds of model spans.
  const groups: Record<string, typeof spans> = {
    "writer OpenAI.chat": spans.filter((s) => s.name === "OpenAI.chat"),
    "judge model.generateText": spans.filter((s) => s.name === "model.generateText"),
  };
  console.log(`project ${PROJECT_NAME}: ${traces.length} traces, ${spans.length} spans ${JSON.stringify(byType)}`);
  for (const [label, group] of Object.entries(groups)) {
    const tokens = group.reduce((n, s) => n + (s.usage?.total_tokens ?? 0), 0);
    const cost = group.reduce((n, s) => n + (s.totalEstimatedCost ?? 0), 0);
    const types = [...new Set(group.map((s) => s.type))].join("/");
    const models = [...new Set(group.map((s) => s.model))].join(",");
    const costed = group.filter((s) => (s.totalEstimatedCost ?? 0) > 0).length;
    console.log(`${label}: ${group.length} spans (type ${types}, model ${models}), with cost ${costed}, tokens ${tokens}, est. cost $${cost.toFixed(4)}`);
  }
  const withPrompt = traces.filter((t) => JSON.stringify(t.metadata ?? {}).includes("opik_prompts")).length;
  console.log(`traces carrying a prompt-library link in metadata: ${withPrompt}`);

  const prompt = await opik.getPrompt({ name: PROMPT_NAME, projectName: PROJECT_NAME });
  const versions = prompt ? await prompt.getVersions() : [];
  console.log(`\nprompt "${PROMPT_NAME}": ${versions.length} versions`);
  for (const v of [...versions].reverse()) {
    console.log(`  ${v.version} commit=${v.commit} "${v.changeDescription}" (${v.prompt.length} chars)`);
  }

  const suite = await opik.getTestSuite(SUITE_NAME, PROJECT_NAME);
  console.log(`\nsuite "${SUITE_NAME}": ${(await suite.getItems()).length} items`);
  const runs = await opik.getTestSuiteExperiments(SUITE_NAME, 100, PROJECT_NAME);
  for (const run of runs) {
    // The experiment record itself holds the prompt-version link the UI shows on the run.
    const exp = await opik.api.experiments.getExperimentById(run.id);
    if (exp.createdAt && exp.createdAt < since) continue;
    const links = (exp.promptVersions ?? []).map((l) => `${l.promptName ?? "?"}@${l.commit}`).join(", ");
    const scores = (run.assertionScores ?? []).map((a) => `${a.name.slice(0, 28)}...=${a.value.toFixed(2)}`).join(" | ");
    console.log(`  run ${run.name}: pass rate ${run.passRate} (${run.passedCount}/${run.totalCount} items), linked prompt: ${links || "none"}`);
    console.log(`     assertion averages: ${scores}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
