# vercel-ai-sveltekit-garden-chat

![TypeScript](https://img.shields.io/badge/typescript-6-3178C6?style=flat&logo=typescript&logoColor=white)
![SvelteKit](https://img.shields.io/badge/sveltekit-3-FF3E00?style=flat&logo=svelte&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.3-2f54eb?style=flat)

**A streaming gardening chatbot in SvelteKit whose every reply is traced, threaded by conversation, and graded by an LLM judge the moment it lands in Opik.**

Streaming chat breaks the usual logging habit. The answer is a stream, not a return value, so there is no line of code where you hold "the reply" and can log it. Every request also re-sends the whole conversation, so request logs fill with near-duplicates. And once the traces exist, somebody still has to read them to know whether the answers were any good.

This example answers all three with Opik. A SvelteKit app streams answers from `gpt-4o-mini`, grounded in a short fictional guide to gardening in the Hollowbrook valley. One OpenTelemetry exporter turns each streamed reply into a trace. The chat id turns traces into threads. And an online evaluation rule, created by a script and enabled before any traffic arrives, has a judge model score every trace as it comes in.

## What you'll build

- **A SvelteKit 3 app** with one page and one endpoint. The page uses the `Chat` class from `@ai-sdk/svelte` (the Svelte package has no `useChat` hook). The endpoint, `src/routes/api/chat/+server.ts`, retrieves the two best-matching sections of `data/garden-guide.md` and calls `streamText` with `gpt-4o-mini`.
- **The Opik hookup** in `src/lib/telemetry.ts`: an `OpikExporter` from `opik-vercel` plugged into an OpenTelemetry `NodeSDK`, plus the AI SDK's `registerTelemetry` call.
- **A rule installer**, `scripts/rule.mjs`, that creates the LLM-as-judge rule `garden_answer_quality` on the project over REST, looking it up by name first so re-runs never duplicate it.
- **A scripted demo**: `npm run demo` ensures the rule, builds and boots the server, plays two multi-turn chats over HTTP while reading the streams, stops the server (which flushes the batched traces), then polls Opik until every trace has its scores.

```
Chat / demo script -> POST /api/chat -> retrieve guide sections -> streamText(gpt-4o-mini)
                                                             \-> OTel spans -> OpikExporter -> Opik trace
Opik server: new trace -> rule "garden_answer_quality" -> judge -> feedback scores on the trace
```

## See it in Opik

Open the **`vercel-ai-sveltekit-garden-chat`** project. After one demo run it holds five `garden-chat-turn` traces, one per question. Each trace has two spans: an `llm` span named `chat gpt-4o-mini` carrying token usage and a dollar cost, and a `general` span named `step 1` for the AI SDK step. A turn costs between $0.00005 and $0.0001 and uses 270 to 450 tokens, and the count climbs along a conversation because the history is re-sent. The streamed reply is complete in the trace even though it left the server token by token.

Open any trace and read the input: it is the full message array, including the system prompt with the guide excerpts that were retrieved for that question. When you open the last trace, the question about a greenhouse heater brand, you can see that the excerpts attached to it were irrelevant, and that the model answered "The Hollowbrook guide does not cover information about greenhouse heater brands or prices" instead of inventing a product.

The **Threads** tab shows two threads: one with 6 messages (three tomato questions: planting date, clay soil, slugs) and one with 4 (blight, then the heater question). The chat id travels from the request through `runtimeContext` to a span attribute, and that is all Opik needs to stitch the turns together.

In the traces table, look at the **Feedback scores** column. Every chat trace carries `answer_relevance` and `stays_in_guide`, both `1` in the verified run, each with a one-sentence reason from the judge (for the heater question: "The reply correctly states that the guide does not cover this information"). They are tagged as online scoring, and nothing in the app's code produced them. In the project's online evaluation rules you will find `garden_answer_quality`, enabled, sampling rate 1.0.

You will also see traces named `online_evaluation` in the same project. They are the judge's own calls, logged by Opik with `llm` spans. The demo filters them out when it counts, and you can too by filtering on name.

## Run it yourself

You need Node 22 or newer, an OpenAI key, and a running Opik server that has an OpenAI key stored under **Settings > AI Providers** (the judge runs on the Opik server and uses that key, not yours from `.env`).

1. `cp .env.example .env` and fill in `OPENAI_API_KEY`. The Opik URL and workspace in the file default to a local server. The example also reads any `.env` in a parent folder.
2. `npm install` (an `.npmrc` is included, see Gotchas)
3. `npm run demo`. It takes about a minute: most of that is waiting for the judge. It exits non-zero if any trace is left unscored after four minutes.
4. Open the project in Opik and look at Traces, Threads, then the online evaluation rule.

To chat yourself instead, run `npm run dev`, open the printed URL, and ask Sprout something. Each browser tab is a new chat id and so a new thread. Offline tests: `npm test`.

## Poke around

- Ask something the guide only half covers ("Can I grow tomatoes in a pot?") and compare `answer_relevance` with `stays_in_guide` in the traces table.
- Edit the judge prompt in `scripts/rule.mjs`, delete the rule in the Opik UI, run `npm run demo` again and watch the new rule score the next batch. Running the demo twice without deleting it creates nothing new.
- Lower `sampling_rate` in the same file to `0.4` and see that only some traces get scores.
- Change `retrieve(query, sections, k = 2)` to `k = 0` in `src/lib/server/garden.ts` so the model gets no excerpts, then watch `stays_in_guide` and the answers' honesty.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-vercel`, then `vite build` fails with `failed to resolve import "zod/v4"`.** The `opik-vercel` package declares a peer range of `opik@^1.8.75`, while the current `opik` release is 2.3.x, so npm refuses the tree. With `legacy-peer-deps=true` in `.npmrc` (included here) the install works, but npm then also skips auto-installing other peers, and `@ai-sdk/provider-utils` needs `zod`. Fix: keep the `.npmrc` and list `"zod": "^4"` in `dependencies`.

**`svelte.config.js` is rejected: `config_file_unsupported`.** SvelteKit 3 no longer reads that file. Pass the config to the plugin instead: `sveltekit({ adapter: adapter() })` in `vite.config.ts`. In the same release `$lib` is gone, which is why the imports here are relative.

**Creating the rule returns `HTTP 400: At least one project must be specified for the automation rule evaluator`.** The REST API takes snake_case JSON. `projectIds` and `samplingRate` are silently ignored; send `project_ids: [projectId]` and `sampling_rate: 1.0`. Look the project up (or create it) first so you have an id before the first trace exists.

**The project shows twice as many traces as you sent.** Opik logs the judge's own LLM calls as traces named `online_evaluation`. Filter on `name = garden-chat-turn` when counting or exporting, as `scripts/verify.mjs` does.

**Tests fail on a fresh clone with `[TSCONFIG_ERROR] Failed to load tsconfig '$app/tsconfig'`.** The project's `tsconfig.json` extends a file that `svelte-kit sync` generates into `.svelte-kit/`, which a clean checkout does not have. Fix: run the sync first. `package.json` has `"prepare": "svelte-kit sync"` and `"pretest": "svelte-kit sync"`, so `npm ci` and `npm test` both do it.

## How it's put together

- `src/routes/+page.svelte`: chat UI built on the `Chat` class.
- `src/routes/api/chat/+server.ts`: parses the request and streams the reply.
- `src/lib/server/chat.ts`: one chat turn, retrieval plus `streamText` with the Opik telemetry settings and the thread id.
- `src/lib/server/garden.ts`: splits the guide into sections, ranks them by word overlap, builds the system prompt.
- `src/lib/telemetry.ts`: `OpikExporter`, `NodeSDK`, `registerTelemetry`, and the thread-id mapping.
- `src/hooks.server.ts`: starts telemetry when the server boots and flushes it on SIGTERM.
- `src/lib/server/env.ts`: loads `.env` files from this folder and its parents.
- `scripts/rule.mjs`: builds and idempotently creates the judge rule over REST.
- `scripts/verify.mjs`: reads traces, spans, cost and scores back from Opik and polls for the judge's scores.
- `scripts/demo.mjs`: the scripted run described above.
- `scripts/env.mjs`: the same `.env` loading for the scripts.
- `data/garden-guide.md`: the fictional Hollowbrook guide the bot answers from.
- `tests/garden.test.ts`: section parsing and retrieval, including the no-match case.
- `tests/rule.test.ts`: rule payload shape, no duplicate creation on re-run, re-enabling a disabled rule.
- `tests/chat.test.ts`: a streamed turn through the Opik-instrumented call with `OPIK_TRACK_DISABLE=true` and a mock model, plus the thread-id mapping.

The tests run offline with no keys and no Opik server: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true npm test`.

---

*built with Opik · inspired by Opik's examples and documentation*
