import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";

/** Load the nearest .env, walking up from this folder (the repo-root .env works too). */
export function loadEnv(): void {
  let dir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  for (;;) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) {
      config({ path: candidate });
      return;
    }
    const parent = dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
