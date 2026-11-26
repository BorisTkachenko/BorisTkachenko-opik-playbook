import * as path from 'node:path';
import * as dotenv from 'dotenv';

// Load this example's .env first, then the repo-root .env. dotenv never
// overrides variables that are already set, so the shell wins over both files.
dotenv.config({
  path: [path.join(__dirname, '..', '.env'), path.join(__dirname, '..', '..', '.env')],
  quiet: true,
});

// The build machine may export base-URL overrides for a local proxy; the
// example always talks to the public OpenAI API.
delete process.env.OPENAI_BASE_URL;

export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}
