import type { Opik } from "opik";
import { CHANGE_NOTES, PROMPT_NAME, PROMPT_V1, PROMPT_V2 } from "./prompts.js";
import { PROJECT_NAME } from "./config.js";

/**
 * Push both wordings to Opik's prompt library as v1 and v2 of one prompt.
 * Every version is immutable and gets a commit hash; the UI shows a v1 -> v2 diff.
 * Safe to re-run: a version that already holds the same text is left alone.
 */
export async function registerPromptVersions(client: Opik): Promise<void> {
  const versions = [
    { version: "v1", text: PROMPT_V1, note: CHANGE_NOTES.v1 },
    { version: "v2", text: PROMPT_V2, note: CHANGE_NOTES.v2 },
  ] as const;

  for (const { version, text, note } of versions) {
    // createPrompt only skips a version when the *latest* one matches, so a re-run
    // would add a v3 that repeats v1. Look the version up first instead.
    const existing = await client.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
    if (existing?.prompt === text) continue;
    if (existing) throw new Error(`${PROMPT_NAME} ${version} already exists with different text`);

    // Each call writes one new immutable version (the first call also creates the prompt).
    // client.createPrompt({ changeDescription }) silently drops the description in this SDK
    // version, so the REST client writes it: the note then shows next to v1 / v2 in the UI.
    await client.api.prompts.createPromptVersion({
      name: PROMPT_NAME,
      projectName: PROJECT_NAME,
      templateStructure: "text",
      version: { template: text, type: "mustache", changeDescription: note },
    });
  }
}
