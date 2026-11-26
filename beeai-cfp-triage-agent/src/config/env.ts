// Load keys from the nearest .env walking up from this folder (the example's own
// .env first, then the repo root).
import { config } from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function loadEnv(): void {
  const paths: string[] = [];
  let dir = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
  for (let i = 0; i < 4; i++) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) paths.push(candidate);
    dir = dirname(dir);
  }
  config({ path: paths, quiet: true });
  // Some dev machines route OpenAI traffic through a local proxy; use the public API.
  delete process.env.OPENAI_BASE_URL;
}

export function requireKey(name: string): void {
  if (!process.env[name]) {
    console.error(`Missing ${name}. Copy .env.example to .env and fill it in.`);
    process.exit(1);
  }
}
