# mastra-banking-agent

**A Mastra retail-banking assistant whose every balance lookup, transaction query and card freeze shows up in Opik as a real `execute_tool` span.**

![Node 22.13+](https://img.shields.io/badge/node-22.13%2B-339933?style=flat&logo=node.js&logoColor=white)
![Mastra core 1.x](https://img.shields.io/badge/%40mastra%2Fcore-1.x-0b0b0b?style=flat)
![Opik OTLP](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

When a banking assistant tells a customer "your card is frozen", you want proof: which tool ran, with which arguments, and what it returned. A chat transcript cannot give you that. This example wires a [Mastra](https://mastra.ai/) agent to Opik through Mastra's OpenTelemetry exporter, so each customer request becomes a trace tree: the agent run, its reasoning steps, the LLM calls with token usage and cost, and the tool calls nested where they happened.

## What you'll build

Tidewater Bank is fictional, and so is its customer (Ines Valadares, two accounts, two cards). One Mastra `Agent` on `gpt-4o-mini` has four tools over a JSON file in `data/`:

- `get_account_balance`
- `list_recent_transactions` (filters: category, merchant, minimum amount, start date, limit)
- `freeze_card`
- `unfreeze_card`

Freezing only flips card state in memory; nothing is written back to disk. The only thing that leaves your machine is the model call. Tracing is configuration in one file (`src/mastra.ts`); the agent, tools and bank logic contain no tracing code.

`npm run demo` plays four requests. The third one makes the model fan out on its own: three tool calls in a single step.

## See it in Opik

Open the `mastra-banking-agent` project. After one run it holds **4 traces**, all named `invoke_agent tidewater-banking-agent`, with 15, 22, 21 and 15 spans. Open the trace for *"How much do I have across checking and savings, and what's the most recent thing that hit savings?"* and expand the tree:

- `invoke_agent` is the root; under it sit `model_generation gpt-4o-mini` and then two `agent_step` spans, one per reasoning round.
- In the first step there is one `chat gpt-4o-mini` span (type **llm**, provider `openai`, 484 tokens, about $0.00012) followed by three **tool** spans: `execute_tool listRecentTransactions` and two `execute_tool getAccountBalance`, one per account. Click one: its input holds the arguments the model chose (for the freeze request, `{"card": "CARD-4417"}`, resolved from "my Visa ending 4417"), and its output holds the JSON the tool returned (`"status": "frozen", "changed": true`).
- The second step is a single `chat` span (650 tokens) that writes the final answer from those results.

The `processor_run` and `model_chunk` spans are Mastra internals and can be collapsed. In the trace list, each of the four traces shows summed token usage (831, 1,134, 1,781 and 871 tokens) and a non-null `total_estimated_cost` of roughly $0.0001 to $0.0003. The whole demo costs under a tenth of a cent.

What this buys you in practice: a wrong answer with correct tool output is a prompt problem; a correct-looking answer built on invented arguments is a grounding problem; a "frozen" claim with no `freeze_card` span is a hallucination. The tool spans tell these apart.

## Run it yourself

1. `cp .env.example .env`, then set `OPENAI_API_KEY` (a repo-root `.env` also works; the demo walks up to find it). The defaults point at a local self-hosted Opik on `http://localhost:5173/api/`, workspace `default`, no Opik key needed.
2. `npm install`
3. `npm run demo` (about 18 seconds)
4. Open the `mastra-banking-agent` project in Opik and click the newest trace.

For Opik Cloud, set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`, `OPIK_API_KEY` and `OPIK_WORKSPACE`.

Offline tests (no keys, no Opik): `OPIK_TRACK_DISABLE=true npm test`. They never import the OTel exporter, so tracing cannot get in their way; `OPIK_TRACK_DISABLE` is the Opik SDK's switch and is harmless here.

## Poke around

- Change the third request to mention an account that does not exist (`SAV-0000`) and look at the tool span: the error object it returned, and how the agent phrases it.
- Ask the agent to freeze a card twice. The second `freeze_card` span returns `"changed": false`.
- Lower `maxSteps` in `src/demo.ts` and compare how many `agent_step` spans a request gets.
- Add a fifth tool (say, `list_cards`) in `src/tools.ts` and watch a new `execute_tool` span name appear.

## Gotchas we hit

**Nothing appears in Opik, and the demo exits 0.** The exporter was set to `protocol: "http/json"`. Opik's OTLP endpoint answers 200 to such a request but ingests nothing, so there is no error to see. Use protobuf and install the matching package:

```ts
new OtelExporter({ provider: { custom: { endpoint: `${base}/v1/private/otel/v1/traces`, protocol: "http/protobuf", headers } } })
// npm i @opentelemetry/exporter-trace-otlp-proto
```

**The trace's Output column is empty.** Mastra's OTel mapping puts the agent's answer on the root span's input attributes, under `mastra.agent_run.output`, and leaves the trace-level output unset. The text is there (open the trace's Input and scroll), just not in the Output column. This example does not patch it.

**Cost is `null`.** Opik prices a span only when it recognises the model and provider. Here Mastra's `chat` spans carry `gen_ai.*` attributes that Opik maps to provider `openai` with the model `gpt-4o-mini-2024-07-18`, so cost is filled in. Only the `chat` llm spans carry usage and cost; the trace rolls them up. With a model Opik's price table lacks, expect usage without a dollar figure.

**Wrong project or workspace.** The project comes from the `projectName` header and the workspace from `Comet-Workspace`; set both in the exporter's `headers`. A local Opik needs no `Authorization` header, so the config only adds it when `OPIK_API_KEY` is set.

## How it's put together

- `data/accounts.json`: the fictional customer, two accounts, two cards, twelve transactions.
- `src/bank.ts`: plain functions for balance, filtered transactions and card status; in-memory state.
- `src/tools.ts`: the four Mastra tools wrapping those functions.
- `src/agent.ts`: the Tidewater agent: instructions, model, tools.
- `src/mastra.ts`: the Mastra instance and the Opik OTLP exporter (the only tracing code).
- `src/demo.ts`: loads env, runs four requests, shuts the exporter down so spans flush.
- `tests/bank.test.ts`: vitest checks for the filters, the idempotent freeze, and the tools called directly.

---

*built with Opik · inspired by Opik's examples and documentation*
