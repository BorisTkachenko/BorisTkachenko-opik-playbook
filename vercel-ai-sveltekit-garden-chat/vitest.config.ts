import { defineConfig } from "vitest/config";

// Unit tests are plain TypeScript, so they skip the SvelteKit plugin entirely.
export default defineConfig({ test: { include: ["tests/**/*.test.ts"] } });
