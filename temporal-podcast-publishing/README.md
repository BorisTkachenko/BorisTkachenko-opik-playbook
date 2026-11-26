# temporal-podcast-publishing

*One Opik trace for a Temporal workflow that spans two processes, including the upload that failed twice before it worked.*

![Node](https://img.shields.io/badge/node-20.3%2B-5FA04E?style=flat&logo=nodedotjs&logoColor=white)
![Temporal SDK](https://img.shields.io/badge/%40temporalio-1.13%2B-000000?style=flat)
![opik](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)

Publishing a podcast episode sounds like one job and is really four: write show notes, write a social post, push files to a CDN, tell the world. Each step can fail on its own, which is exactly what Temporal is for. The catch for observability is that the process that *starts* the workflow and the process that *runs* it are different programs, often on different machines. A trace that begins in one of them normally ends there.

This example publishes two episodes of a made-up indie show, *Burnt Toast & Backroads*, and makes the Opik trace follow the work across the process boundary. The CDN step is rigged to fail, so you can see what a retry looks like in a trace.

## What you'll build

- A `publishEpisode` workflow with three activities: `draftShowNotes` and `draftSocialBlurb` (both `gpt-4o-mini`, reading a transcript from `data/`) and `uploadToCdn`, a stand-in uploader that throws on its first attempt or two.
- `npm run demo`, which starts a throwaway in-memory Temporal dev server, spawns the worker as a second OS process, publishes both episodes from the starter, and tears everything down.
- Tracing with the Opik TypeScript SDK: the starter creates the trace, the worker attaches its spans to it, `opik-openai` wraps the OpenAI client, and a feedback score records how many attempts the upload needed.
- `npm run verify`, which reads the project back from Opik and checks the shape described below.

How the trace crosses the boundary: the starter opens a trace and one span, then stores `{ traceId, parentSpanId }` in the workflow input. Temporal delivers that input to the worker like any other argument. Each activity attempt opens its own span under that parent. No collector, no header propagation.

```
starter process                          worker process
publish-episode:ep41  (trace)
  temporal:publishEpisode  (span)  --ids in workflow input-->
                                           draftShowNotes (attempt 1)  -> OpenAI call
                                           draftSocialBlurb (attempt 1) -> OpenAI call
                                           uploadToCdn (attempt 1)  ERROR
                                           uploadToCdn (attempt 2)  ERROR
                                           uploadToCdn (attempt 3)  ok
```

## See it in Opik

Open the **temporal-podcast-publishing** project and the **Traces** tab. After one run there are two traces, `publish-episode:ep41` and `publish-episode:ep42`, each with a `cdn_upload_attempts` feedback score column (3 and 2).

Click `publish-episode:ep41`. In the final run it had 8 spans: a `temporal:publishEpisode` span at the top, and under it the worker's work. `draftShowNotes (attempt 1)` contains a `draft-show-notes` child with the transcript prompt, the JSON the model returned and 848 tokens; `draftSocialBlurb (attempt 1)` does the same with 173 tokens. Then three `uploadToCdn` spans of type tool, in order: attempt 1 and attempt 2 both red with the error `CDN edge returned 503 Service Unavailable (upload part 3 of 4)`, attempt 3 clean. Open any worker span's metadata and you will find `process.role = worker` and a pid; the trace's own metadata says `starter` with a different pid. That is the proof the tree was assembled from two processes. Total cost on the trace was about $0.00026.

`publish-episode:ep42` is the milder story: 7 spans, one red `uploadToCdn (attempt 1)` (`connection reset by peer`) and a green attempt 2.

Two things to notice. The LLM spans appear once each even though the upload retried twice, because Temporal does not re-run a completed activity; you never pay for the drafts again. And a retry that "eventually worked" is easy to miss in Temporal's own UI. Here it is a red span you can filter on, and the feedback score lets you sort episodes by how hard the CDN fought back.

## Run it yourself

1. `cd temporal-podcast-publishing && cp .env.example .env`, then fill in `OPENAI_API_KEY` (a repo-root `.env` is picked up too). For self-hosted Opik leave `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`; for Opik Cloud add your `OPIK_API_KEY` and workspace.
2. `npm install`
3. `npm run demo` (about 17 seconds, roughly $0.0005 of `gpt-4o-mini`). The first run may download the Temporal dev server; the demo uses port 7243, override with `TEMPORAL_PORT`.
4. `npm run verify` to print each trace as a tree and assert the checks.
5. Open the project in Opik.

To use your own Temporal server instead, run `npm run worker` with `TEMPORAL_ADDRESS` set and start `publishEpisode` on the `podcast-publishing` task queue; remember the trace link has to be put in the input as `demo.ts` does, otherwise the activities run untraced.

## Poke around

- In `src/activities.ts` raise `ep42`'s `count` to 4 and rerun: four red upload spans, then a green one. Set it to 5 and the workflow runs out of attempts (`maximumAttempts` is 5) and fails; look at how the starter's span ends in that case.
- Change `backoffCoefficient` in `src/workflows.ts` and read the gaps between attempt spans on the timeline.
- Edit the system prompt in `draftSocialBlurb` to ask for hashtags and compare the two `draft-social-blurb` spans across runs.
- Add `trace.score` calls in `demo.ts` for something else you care about, such as the blurb's character count, and sort the Traces table by it.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.61" from opik-openai@2.3.4`.** `opik` and `opik-openai` are both at 2.3.4, but the integration's peer range still stops at 1.x. The two work together; npm just refuses. Add an override so a plain `npm install` succeeds:

```json
"overrides": { "opik-openai": { "opik": "$opik" } }
```

**Re-creating the trace from the worker erases its input and metadata.** The obvious way to join a trace from a second process is `opik.trace({ id: traceId, name })`. That sends a second create for the same id, and the later write wins: in a probe, the trace came back with `input: null` and `metadata: null` and kept only the output. Build the handle without the network call instead. `src/tracing.ts` switches tracing off for that one synchronous line with `setTracingActive(false)`, restores the previous state, and then calls `.span()` on the handle, which is sent normally.

**The OpenAI spans say `general`, not `llm`.** `opik-openai` records completions with the span type `general`. They still carry model, provider, token usage and an estimated cost (the verify step asserts a non-zero cost), so cost views work; just don't filter the Spans tab by type `llm` and expect to find them.

## How it's put together

- `src/demo.ts` is the starter: dev server, worker process, trace per episode, feedback score, flush.
- `src/worker.ts` is the worker process; it flushes Opik on shutdown.
- `src/workflows.ts` is the `publishEpisode` workflow and its retry policy.
- `src/activities.ts` holds the two LLM activities, the flaky upload, and the `trackOpenAI` wrapper.
- `src/tracing.ts` is the shared Opik client, the trace-handle trick and the per-attempt span wrapper.
- `src/shared.ts` holds the types and the task queue name; `src/env.ts` loads `.env` files and pins the project name.
- `src/verify.ts` reads the traces back through Opik's REST API and asserts the expected shape.
- `data/` has the two fictional transcripts.
- `tests/` has the offline vitest suite: the outage schedule, traced and untraced upload attempts, show-notes parsing against a stubbed OpenAI client, and the data files. Run `npm test`; it needs no keys and sets `OPIK_TRACK_DISABLE=true` (the SDK's switch to turn tracking off) in `vitest.config.ts`.

---

*built with Opik · inspired by Opik's examples and documentation*
