# voltagent-restaurant-reservations

![Node](https://img.shields.io/badge/node-20.19%2B-339933?style=flat&logo=node.js&logoColor=white)
![VoltAgent](https://img.shields.io/badge/%40voltagent%2Fcore-2.11-1b1f23?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

**A table-booking agent whose traces show what it cost, once its OpenTelemetry attributes speak Opik's language.**

You can point almost any OpenTelemetry exporter at Opik and get traces. Whether those traces are *useful* is another matter. VoltAgent emits spans with its own attribute names (`llm.usage.prompt_tokens`, `llm.model`, `span.type`), and Opik's OTLP ingestion only understands the `gen_ai.*` semantic conventions. The result is a trace tree that looks fine and tells you nothing: every span is `general`, there is no model, no token count and no dollar figure. This example makes that gap visible and closes it with a small exporter wrapper.

## What you'll build

A reservation assistant for Saltmarsh Kitchen, an invented seafood restaurant, running on `gpt-4o-mini`. It has four tools over offline data in `data/restaurant.json` (bookings change in memory only, so every run starts identical):

- `check_table_availability(date, time, party_size)`: free tables, or the three nearest open times when the room is full
- `create_booking(name, date, time, party_size)`
- `cancel_booking(booking_id)`
- `list_dietary_menu(diet, course?)`

`npm run demo` plays four scripted guests, flushes the OpenTelemetry exporter and exits. No server is started.

## See it in Opik

Open the `voltagent-restaurant-reservations` project. There are four traces, all named `saltmarsh-reservations`, one per conversation. Open the second one ("book 4 for Dec 5th at 21:00 under the name Alvarez"):

- The **trace** input is the guest's sentence and its output is the assistant's confirmation, not a dump of attributes.
- Under it sits a `general` agent span, an `llm` span called `llm:generateText`, and two `tool` spans: `tool.execution:check_table_availability` with input `{"date":"2026-12-05","time":"21:00","party_size":4}`, and `tool.execution:create_booking` with `{"name":"Alvarez",...}` returning booking `BK-2001` on table `T3`.
- The `llm` span shows model `gpt-4o-mini`, provider `openai`, 622 prompt + 42 completion = 664 tokens and an estimated cost of $0.0001185. The four traces carry 565, 664, 695 and 533 tokens (2,457 in total, about $0.00047), and each trace total equals the sum of its llm spans, so nothing is counted twice.
- Conversation 1 ends with the agent offering 18:00, 17:30 or 20:30 because `check_table_availability` returned `available: false` for four people at 19:00. The cancel in conversation 4 shows `BK-1004` (the Brennan party) leaving the book.

**The before picture.** Run `OPIK_GENAI_MAPPING=off npm run demo` and open the traces again. The same four trees arrive, but every span is `general`, model and provider are empty, the Usage and Cost columns are blank, the trace token total is empty, and the trace input is a JSON blob of ids (`operation.id`, `entity.id`, `agent.instructions`...). That is what an unmapped VoltAgent looks like in Opik.

One thing is not filled in: the `llm` span has an input (the message list) but no output. VoltAgent puts the final answer on the agent span, so it appears there and as the trace output.

## Run it yourself

You need Node 20.19+ and an OpenAI key. For a local Opik, `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` come from the repo-root `.env`.

1. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-root `.env` is picked up too).
2. `npm install`
3. `npm run demo` (about 20 seconds, well under a cent)
4. Open the `voltagent-restaurant-reservations` project in Opik.

Tests need no keys and no Opik: `env -u OPENAI_API_KEY OTEL_SDK_DISABLED=true npm test` (`OTEL_SDK_DISABLED=true` is OpenTelemetry's switch for turning the SDK off). Type-check with `npm run typecheck`.

## Poke around

- Re-run with `OPIK_GENAI_MAPPING=off` and compare against a mapped run, as above.
- In `src/genai-mapping.ts`, delete the `gen_ai.system` / `gen_ai.provider.name` lines but keep the model and usage copies. Then check the cost column: it is the number that depends on Opik resolving both model and provider.
- Ask for something the tool cannot give: edit a conversation to request 18:15. `check_table_availability` returns an error about the half-hour grid and the agent has to recover.
- Switch `MODEL` in `src/agent.ts` to another cheap model and watch whether Opik still prices the llm span; if you change vendor, also pass the new provider name to `mapToGenAI`.

## Gotchas we hit

**Every span is `general` and usage and cost are empty.** Cause: VoltAgent's attribute names (`llm.model`, `llm.usage.*`, `span.type`) are not in Opik's OTLP mapping, and without a recognised provider attribute Opik will not price a span. Fix: copy them to `gen_ai.request.model`, `gen_ai.system` plus `gen_ai.provider.name`, and `gen_ai.usage.{prompt,completion,total}_tokens` before export, as `mapToGenAI` in `src/genai-mapping.ts` does.

**Span inputs are a wall of ids even after the mapping works.** Cause: Opik files every attribute it does not recognise into the span *input*, and VoltAgent attaches `operation.id`, `entity.*`, `agent.instructions`, `llm.*`, `usage.prompt_context.*` and more to every span. Fix: after copying, delete those keys (the `NOISE` pattern). For tool spans, VoltAgent stores the arguments as a JSON string in `input`; mirror it to `gen_ai.tool.call.arguments` and delete `input`, or the arguments are merged in twice.

**The agent span carries summed token counts.** VoltAgent also writes `usage.prompt_tokens` and friends on the root span. Mapping those to `gen_ai.usage.*` would make Opik treat the agent span as a second LLM call and double the trace totals. The mapper deletes them instead; the check is that each trace total equals its llm span.

**`npm install` fails with `ERESOLVE` on the OTLP exporter.** Cause: the newest `@opentelemetry/exporter-trace-otlp-proto` pins a different `@opentelemetry/api` range than the 0.204 OTel packages inside `@voltagent/core`. Fix: install the matching exporter, `@opentelemetry/exporter-trace-otlp-proto@0.204.0`, with `@opentelemetry/sdk-trace-base@^2` (VoltAgent needs the OTel 2.x APIs).

## How it's put together

- `data/restaurant.json`: six tables, seven existing bookings, a nine-item menu tagged by diet.
- `src/restaurant.ts`: availability, booking, cancellation and menu logic over that data (pure, in memory).
- `src/tools.ts`: the four tools as zod-typed VoltAgent tools.
- `src/agent.ts`: the agent, its instructions and model.
- `src/observability.ts`: the OTLP http/protobuf exporter aimed at Opik's OTel endpoint, with the project and workspace headers.
- `src/genai-mapping.ts`: the attribute mapping and the exporter wrapper that applies it.
- `src/demo.ts`: loads env, runs the four conversations, shuts the SDK down so the last spans are flushed, exits.
- `tests/restaurant.test.ts`, `tests/mapping.test.ts`: offline tests for the logic, the tools run directly with the SDK disabled, and the mapping.

*built with Opik · inspired by Opik's examples and documentation*
