import adapter from "@sveltejs/adapter-node";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

// SvelteKit 3 takes its config here (svelte.config.js is rejected). adapter-node emits a plain
// `node build` server, which is what `npm run demo` boots.
export default defineConfig({
  plugins: [sveltekit({ adapter: adapter() })],
});
