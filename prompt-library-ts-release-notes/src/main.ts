import { PROJECT_NAME } from "./config.js"; // sets OPIK_PROJECT_NAME first; keep this import on top
import { Opik, flushAll, runTests } from "opik";
import { type ChangeList, loadChangeLists } from "./changelogs.js";
import { registerPromptVersions } from "./library.js";
import { PROMPT_NAME } from "./prompts.js";
import { ensureSuite } from "./suite.js";
import { makeReleaseNoteWriter } from "./traced.js";
import { MODEL } from "./writer.js";

const JUDGE_MODEL = "gpt-4.1-mini";

async function main(): Promise<void> {
  const opik = new Opik({ projectName: PROJECT_NAME });
  const writeNote = makeReleaseNoteWriter(opik);

  // 1. Prompt library: v1 and v2 of the same prompt.
  await registerPromptVersions(opik);

  // 2. One traced call with the newest version, so there is a trace to open.
  const sample = loadChangeLists()[4] as ChangeList;
  console.log(`tidepool ${sample.version} (latest prompt)\n${await writeNote(sample, "v2")}\n`);

  // 3. The test suite: same items and assertions for every prompt version.
  const suite = await ensureSuite(opik);

  // 4. Run the suite once per version. Each run is an experiment linked to the prompt version it tested.
  const results = [];
  for (const version of ["v1", "v2"]) {
    const prompt = await opik.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
    if (!prompt) throw new Error(`missing prompt ${version}`);
    const result = await runTests({
      testSuite: suite,
      // The task receives each suite item's data and returns what the judges will read.
      task: async (item) => {
        const entry = item as unknown as ChangeList;
        return { input: { change_list: entry.changes, version: entry.version }, output: await writeNote(entry, version) };
      },
      experimentName: `${PROMPT_NAME}-${version}`,
      experimentConfig: { prompt_version: version, prompt_commit: prompt.commit, model: MODEL },
      // prompts links the experiment to this exact prompt version in the Opik UI.
      prompts: [prompt],
      // Model for the LLM judges that evaluate the assertions.
      model: JUDGE_MODEL,
      taskThreads: 5,
    });
    results.push({ version, result });
  }

  console.log("=== Prompt version comparison ===");
  for (const { version, result } of results) {
    const rate = result.passRate === undefined ? "n/a" : `${Math.round(result.passRate * 100)}%`;
    console.log(`${PROMPT_NAME} ${version}: ${rate} pass rate (${result.itemsPassed}/${result.itemsTotal} items)  ${result.experimentUrl ?? ""}`);
  }

  // Traces and spans are sent in batches; without a flush the process can exit first.
  await flushAll();
  await opik.flush();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
