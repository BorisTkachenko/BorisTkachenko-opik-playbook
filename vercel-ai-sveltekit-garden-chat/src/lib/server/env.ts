import { config } from "dotenv";
import fs from "node:fs";
import path from "node:path";

// Load this folder's .env, then walk up and load the nearest parent .env (the repo-root one
// that holds shared keys). Variables already in the environment always win.
export function loadEnv(start = process.cwd()): void {
  let dir = path.resolve(start);
  for (;;) {
    const file = path.join(dir, ".env");
    if (fs.existsSync(file)) config({ path: file, quiet: true });
    const parent = path.dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
