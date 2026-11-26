import { config } from "dotenv";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Load this folder's .env, then every parent .env up to the filesystem root (the repo-root one
// carries the shared keys). Already-set variables win, so the Opik run wrapper's values stick.
export function loadEnvFiles(start = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")) {
  let dir = start;
  for (;;) {
    const file = path.join(dir, ".env");
    if (fs.existsSync(file)) config({ path: file, quiet: true });
    const parent = path.dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
