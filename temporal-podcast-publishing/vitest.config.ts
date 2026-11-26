import { defineConfig } from 'vitest/config';

export default defineConfig({ test: { include: ['tests/**/*.test.ts'], env: { OPIK_TRACK_DISABLE: 'true' } } });
