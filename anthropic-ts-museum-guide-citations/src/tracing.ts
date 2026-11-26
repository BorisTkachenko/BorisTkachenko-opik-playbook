import { Opik, flushAll, setGlobalClient } from "opik";

export const PROJECT_NAME = "anthropic-ts-museum-guide-citations";

// `track` builds its own internal client from the environment and ignores setGlobalClient, so the
// project must be set here too, or its traces land in "Default Project".
process.env["OPIK_PROJECT_NAME"] = PROJECT_NAME;

// Client for explicit calls (suites, datasets). URL and workspace come from OPIK_URL_OVERRIDE /
// OPIK_WORKSPACE in the environment.
export const opik = new Opik({ projectName: PROJECT_NAME });
setGlobalClient(opik);

// Several clients batch in the background (this one and the one behind `track`); flushAll drains all
// of them, so a short script does not exit with traces still queued.
export const flush = flushAll;
