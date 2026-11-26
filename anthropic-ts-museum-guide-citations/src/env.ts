import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

// Walk up from this folder to the nearest .env, so the example works both from a
// standalone clone (.env next to package.json) and from a repo that keeps one at its root.
let dir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
for (;;) {
  const candidate = join(dir, ".env");
  if (existsSync(candidate)) {
    dotenv.config({ path: candidate });
    break;
  }
  const parent = dirname(dir);
  if (parent === dir) break;
  dir = parent;
}

// A dev shell may route Anthropic traffic through a proxy; this example talks to the API directly.
delete process.env["ANTHROPIC_BASE_URL"];
