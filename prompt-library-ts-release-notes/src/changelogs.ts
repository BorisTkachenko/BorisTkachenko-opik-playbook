import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export interface ChangeList {
  tool: string;
  version: string;
  changes: string[];
}

const here = dirname(fileURLToPath(import.meta.url));

/** The fictional changelog entries for the "tidepool" CLI. */
export function loadChangeLists(): ChangeList[] {
  return JSON.parse(readFileSync(join(here, "..", "data", "changelogs.json"), "utf8")) as ChangeList[];
}

/** Render one change list as the user message sent to the model. */
export function formatChangeList(entry: ChangeList): string {
  const bullets = entry.changes.map((c) => `- ${c}`).join("\n");
  return `${entry.tool} ${entry.version}\n${bullets}`;
}
