# beeai-cfp-triage-agent

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6) ![BeeAI](https://img.shields.io/badge/BeeAI_framework-0.1.13-orange) ![Tracing](https://img.shields.io/badge/tracing-OpenInference_%E2%86%92_OTLP_%E2%86%92_Opik-blue)

A ReAct agent that triages talk proposals for a fictional conference, and the glue that makes its reasoning loop readable in Opik.

## Why this exists

Conference chairs read hundreds of abstracts before they decide anything. An agent can do the first pass (is the speaker reliable, is there room in the track, is the abstract any good, did someone already submit this?), but a recommendation like "waitlist" is only trustworthy if you can see which facts it rested on. A ReAct agent loops: think, call a tool, read the result, think again. Without tracing, that loop is invisible.

BeeAI Framework has an OpenInference instrumentation, so the loop can be exported as OpenTelemetry spans to Opik. Out of the box the result is usable but rough: no cost, tools typed as generic spans, a trace input buried under bookkeeping fields. This example shows the loop in Opik and the small span processor that cleans it up.

## What you'll build

For the fictional *Hollowbrook DevDays* CFP (everything lives in `data/`, nothing leaves your machine except the model call):

- four tools the agent can call: `speaker_history`, `track_capacity`, `score_abstract`, `flag_duplicate`
- a ReAct agent on `gpt-4o-mini` that calls each tool and answers `Recommendation: accept | waitlist | reject` with reasons
- a CLI: `list`, `triage <id>`, `demo` (three proposals), `verify` (reads the traces back from Opik and checks them)
- `src/telemetry/`: the OTLP exporter, the BeeAI instrumentation and an attribute mapper that renames spans' attributes into the ones Opik understands

## See it in Opik

Run the demo, then open the **beeai-cfp-triage-agent** project and the **Traces** tab. You get one trace per proposal (three for the demo), each named `beeai-framework-main`.

- **Trace input** is the full reviewer prompt including the proposal text; **output** is the plain-text recommendation (for example `Recommendation: accept / Slot: Thu 14:00 / Reasons: ...`).
- Open a trace. In our run each one had **74 spans**: 5 `iteration-N` groups, 16 `tool` spans, 9 or 10 `llm` spans and the rest `general` (BeeAI's per-event `agent.react.update*` / `partialUpdate*` spans).
- Inside `iteration-1` you will see `backend.openai.chat.start-1` (the call going out), `backend.openai.chat.success-1` (the reply), then the tool call: `tool.dynamic.speakerHistory.start` / `.success`. The `success` span carries the tool's JSON result as its output. Iterations 2-4 do the same for `trackCapacity`, `scoreAbstract` and `flagDuplicate`; iteration 5 is the final answer.
- Each tool call shows up as four `tool` spans (BeeAI's `agent.react.toolStart`/`toolSuccess` wrappers plus the `tool.dynamic.*` pair). That is how the instrumentation emits it, not duplicated work.
- Click an `llm` `...success` span: provider `openai`, model `gpt-4o-mini`, prompt/completion/total tokens and an estimated cost (about $0.0002-0.0003).
- Trace totals in our run: 3,115 / 3,117 / 2,971 tokens and roughly $0.00053-0.00056 per proposal.

Honest caveat: only **2 of the 5** llm calls in each trace report token counts (BeeAI attaches them to some events only), so the usage and cost columns undercount real spend. The trace total equals the sum of the llm spans that do report, so nothing is double counted.

## Run it yourself

1. Install: `npm install` (needs Node 20+).
2. Copy `.env.example` to `.env` (or put the keys in a `.env` further up the tree, which is searched too) and set `OPENAI_API_KEY`. Point `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` at your Opik; for Opik Cloud also set `OPIK_API_KEY`.
3. Run the three-proposal demo (about 25 seconds): `npm run demo`
4. Read the traces back and check them: `npm run verify` (add `-- --since 2026-01-01T00:00:00` to skip older traces). It prints, per trace, the span counts by type, the llm spans with usage and cost, and whether the trace total matches the sum of its llm spans.
5. One proposal only: `npm run triage -- P-1005`. List proposals: `npx tsx src/cli.ts list`.
6. Offline tests, no keys needed: `npm test` (set `OTEL_SDK_DISABLED=true` to keep the exporter off; the tracing test sets it itself).

Expected `verify` shape:

```
project beeai-cfp-triage-agent: 3 traces
01a21761-...  spans=74 {"general":49,"tool":16,"llm":9}  iterations=5
   llm spans with usage=2 priced=2  trace tokens=3115 sum(llm)=3115 OK
VERIFY OK
```

## Poke around

- Triage `P-1004` and `P-1005`: they are near-identical abstracts from different speakers. Compare the `flagDuplicate.success` outputs and the final reasons. Model verdicts vary between runs (we saw `waitlist` and `reject` for the same proposal).
- Triage `P-1003` (a vague abstract, first-time speaker): the `scoreAbstract` span shows a total of 2/20.
- Edit `data/tracks.json` to open a slot in the `ml` track, rerun `P-1005`, and watch iteration 2's `trackCapacity` output change.
- Remove `OpikAttributeMapper` from `spanProcessors` in `src/telemetry/index.ts` and rerun: cost disappears, tools turn `general`, trace input gets noisy.

## Gotchas we hit

**No traces, and no project appears in Opik, though the run printed "Done".**
`@arizeai/openinference-instrumentation-beeai` only patches `beeai-framework` versions `>=0.1.9 <0.1.14`. On `0.1.32` the patch is skipped with a debug-level warning, so no BeeAI spans exist to export. Fix: pin the framework in `package.json`: `"beeai-framework": "0.1.13"` (with `@ai-sdk/openai` `^1.3.13`).

**`total_estimated_cost` is empty on llm spans even though tokens are shown.**
Opik prices a span only when model, provider and usage are on the same span. OpenInference puts `llm.model_name` on the `start` event and `llm.token_count.*` on the `success` event, and never sets a provider. The mapper copies the model across and sets `gen_ai.system=openai` (see `src/telemetry/mapper.ts`).

**Tool calls appear as `general` spans, and the trace input is a pile of `source`, `traceId`, `history`.**
Opik types a span `tool` from `gen_ai.tool.call.arguments` / `gen_ai.tool.call.result`, and puts any attribute it has no rule for into the span input. The mapper sets the two tool attributes from `tool.parameters` / `output.value`, and moves every unrecognised attribute under `opik.metadata.*`, so input is the prompt and output is the answer.

**Each llm span carries ~130 `llm.output_messages.N.*` attributes.**
BeeAI streams the reply token by token and the instrumentation records every chunk. They duplicate `output.value`, so the mapper drops them.

**`npm install` fails with `ERESOLVE unable to resolve dependency tree`.**
`beeai-framework` declares dozens of optional peers (LangChain, Zep, Elasticsearch...) whose ranges conflict with each other. None are needed here. The committed `.npmrc` contains `legacy-peer-deps=true`, which makes npm skip peer resolution; keep it if you copy the project.

## How it's put together

- `src/cli.ts`: `list | triage | demo | verify` entry point; starts tracing before BeeAI is imported and flushes at the end.
- `src/agent/triage.ts`: builds the ReAct agent and runs one proposal. `src/agent/prompt.ts`: the reviewer prompt.
- `src/tools/*.ts`: one file per tool (speaker history, track capacity, abstract scoring, duplicate flagging); each exports a plain function plus the BeeAI tool.
- `.npmrc`: `legacy-peer-deps=true`, see the install gotcha above.
- `src/data/store.ts`, `data/*.json`: the offline CFP (8 proposals, 6 speakers, 4 tracks).
- `src/config/env.ts`: loads `.env` from this folder or any parent.
- `src/telemetry/index.ts`: OTLP/protobuf exporter, BeeAI instrumentation, batch flush on shutdown.
- `src/telemetry/mapper.ts`: the span processor that fixes model, provider, tool typing and input/output.
- `src/telemetry/verify.ts`, `project.ts`: reads traces back via Opik's REST API and checks them; shared project name.
- `tests/tools.test.ts`, `tests/mapper.test.ts`, `tests/tracing-disabled.test.ts`: tool logic, attribute mapping, and an instrumented tool call with tracing off.

*built with Opik · inspired by Opik's examples and documentation*
