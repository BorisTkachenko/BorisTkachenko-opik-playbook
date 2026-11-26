# voltagent-restaurant-reservations

A VoltAgent reservation assistant for a fictional restaurant, traced to Opik over OpenTelemetry. Run `npm run demo` and four scripted guest conversations land as traces with llm spans (model, token usage, cost) and tool spans (arguments and results).

## Run it

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or use the repo-root `.env`).
2. `npm install`
3. `npm run demo`
4. Open the `voltagent-restaurant-reservations` project in Opik.

## What the mapping does

VoltAgent's spans are OpenTelemetry spans, but they use their own attribute names (`llm.usage.prompt_tokens`, `llm.model`, `span.type`). Opik reads the `gen_ai.*` conventions, so without a rename every span is `general` with no model, usage or cost. `src/genai-mapping.ts` copies the attributes across just before export; `OPIK_GENAI_MAPPING=off` turns it off so you can compare.

## Tests

`OTEL_SDK_DISABLED=true npm test` runs offline with no keys.

## Files

- `src/restaurant.ts`, `data/restaurant.json`: reservation logic and the fictional data.
- `src/tools.ts`, `src/agent.ts`, `src/demo.ts`: tools, agent, scripted conversations.
- `src/observability.ts`: OTLP exporter aimed at Opik.
- `src/genai-mapping.ts`: the `gen_ai.*` attribute mapping.
- `tests/`: logic and mapping tests.
