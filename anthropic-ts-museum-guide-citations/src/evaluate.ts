import "./env.js";
import { runTests } from "opik";
import { askGuide, MODEL, NOTES } from "./guide.js";
import { verifyQuotes } from "./notes.js";
import { GLOBAL_ASSERTIONS, toSuiteItems } from "./suite.js";
import { flush, opik, PROJECT_NAME } from "./tracing.js";

const SUITE_NAME = "museum-guide-citation-suite";

// A test suite is a dataset whose items carry plain-English assertions. Creating it (idempotently)
// makes it appear under the project's Test suites tab; global assertions apply to every item, and the
// execution policy runs each item 3 times, passing it if 2 runs pass, so one flaky judge verdict
// doesn't flip an item.
const suite = await opik.getOrCreateTestSuite({
  name: SUITE_NAME,
  projectName: PROJECT_NAME,
  globalAssertions: GLOBAL_ASSERTIONS,
  globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
});
// Inserting re-sends the same items; Opik de-duplicates identical content, so re-runs don't pile up.
await suite.insert(toSuiteItems(NOTES));

// runTests answers every item through the guide, has the judge grade every assertion, and records the
// whole thing as one suite run (an experiment) with pass/fail per item and the judge's reason.
const result = await runTests({
  testSuite: suite,
  task: async (item) => {
    const question = String(item["question"]);
    // Return exactly what the model saw (question + notes) so the judge has the source in hand.
    return { input: { question, context: NOTES }, output: await askGuide(question) };
  },
  model: MODEL, // the judge; no reasoning_effort override, which the judge call rejects
  taskThreads: 3,
  projectName: PROJECT_NAME,
  experimentConfig: { prompt: process.env["LAX_GUIDE"] === "1" ? "lax" : "strict", model: MODEL },
  experimentName: `${process.env["LAX_GUIDE"] === "1" ? "lax-guide" : "guide"}-${new Date().toISOString().slice(0, 16)}`,
});

console.log(`\nPass rate: ${((result.passRate ?? 0) * 100).toFixed(0)}% (${result.itemsPassed}/${result.itemsTotal} items passed)`);
for (const item of result.itemResults.values()) {
  const first = item.testResults[0];
  const question = (first?.testCase.taskOutput["input"] as { question: string }).question;
  const output = String(first?.testCase.taskOutput["output"] ?? "");
  const local = verifyQuotes(output, NOTES);
  console.log(`  [${item.passed ? "PASS" : "FAIL"}] ${question}  (${item.runsPassed}/${item.runsTotal} runs, local quote check ${local.filter((q) => q.verbatim).length}/${local.length})`);
  if (item.runsPassed < item.runsTotal) {
    for (const run of item.testResults)
      for (const s of run.scoreResults)
        if (s.scoringFailed || s.value !== 1) console.log(`         failed: ${s.name} — ${s.reason}`);
  }
}
if (result.experimentUrl) console.log(`\nView the run: ${result.experimentUrl}`);

await flush();
