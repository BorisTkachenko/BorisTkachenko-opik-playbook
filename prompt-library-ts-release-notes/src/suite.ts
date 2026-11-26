import type { Opik, TestSuite } from "opik";
import { loadChangeLists } from "./changelogs.js";
import { PROJECT_NAME, SUITE_NAME } from "./config.js";

/** The quality bar, as plain-language assertions. An LLM judge checks each one per reply. */
export const ASSERTIONS = [
  "The reply contains no emoji and no exclamation marks anywhere (headline or summary)",
  "The headline names a concrete change from the change list (a specific command, flag, number or removal) and uses no hype words such as 'revolutionary', 'game-changing', 'supercharge' or 'blazing'",
  "The summary is at most 2 sentences long",
];

/**
 * Create the test suite once and load the five change lists into it.
 * The suite stores the assertions, so both prompt versions are judged by the same rules.
 */
export async function ensureSuite(opik: Opik): Promise<TestSuite> {
  const suite = await opik.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    description: "Release-note headline rules: plain text, concrete headline, short summary",
    globalAssertions: ASSERTIONS,
    // Judges are LLMs and occasionally disagree with themselves: each reply is judged on 3
    // independent runs and the item passes when 2 of them pass.
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // insert() does not dedupe, so only seed an empty suite.
  if ((await suite.getItems()).length === 0) {
    await suite.insert(
      loadChangeLists().map((entry) => ({
        data: { tool: entry.tool, version: entry.version, changes: entry.changes },
        description: `${entry.tool} ${entry.version}`,
      })),
    );
  }
  return suite;
}
