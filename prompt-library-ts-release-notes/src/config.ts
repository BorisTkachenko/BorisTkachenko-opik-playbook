import { loadEnv } from "./env.js";

export const PROJECT_NAME = "prompt-library-ts-release-notes";
export const SUITE_NAME = "release-note-headline-rules";

loadEnv();
// track() uses its own global client and ignores any client you construct, so the
// project has to come from the environment. Without this line every trace lands in
// "Default Project". This module must be imported before anything that imports "opik".
process.env.OPIK_PROJECT_NAME = PROJECT_NAME;
