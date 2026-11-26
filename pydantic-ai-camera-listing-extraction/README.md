# pydantic-ai-camera-listing-extraction

**Does your extraction agent read the listing, or write one?** A Pydantic AI agent fills a typed `CameraListing` from messy vintage-camera marketplace posts, Opik traces it over OpenTelemetry, and a test suite fails every item where a value was made up.

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/Pydantic%20AI-OTel%20traced-E92063?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

Typed output feels safe: if the model returns a valid `CameraListing`, it must be right. But a schema only guarantees the *shape* of the answer. A post that says "asking 180 EUR" produces a perfectly valid `price_usd: 180.0`, and a post that never names a city can come back with `location: "EU"`. Nothing crashes, so the only way to find out is to compare each field with the post, which is exactly what a test suite is for.

## What you'll build

- `listing_agent.py`: a Pydantic AI `Agent` on `gpt-4o-mini` with `output_type=CameraListing` (brand, model, mount, condition, price in USD, shutter count, included accessories, location) and one tool, `check_mount`.
- `data/posts.json`: six fictional posts. Some are complete; others deliberately leave out the price, the shutter count, the mount or even the brand. Each carries the true values and a few plain-language assertions.
- `tracing.py`: sends Pydantic AI's OpenTelemetry spans to Opik's OTLP endpoint, with a `projectName` header so they land in this project and `OpikSpanProcessor` so they join the `@opik.track` trace.
- `main.py`: extracts every post, prints which fields were invented or missed (a plain-Python check, no model), then runs the same posts as an Opik test suite with an LLM judge, three runs per item.

## See it in Opik

Open the project `pydantic-ai-camera-listing-extraction`. After one run it holds 24 traces: 6 named `extract_listing` (the plain extraction pass) and 18 named `evaluation_task` (3 runs for each of the 6 suite items).

Open an `extract_listing` trace. Its tree is `extract_listing` (the root) > `invoke_agent agent` > `chat gpt-4o-mini` (type llm) and `execute_tool check_mount` (type tool). The llm span shows provider `openai`, model `gpt-4o-mini-2024-07-18`, token usage (412 prompt and 95 completion tokens on one of ours) and an estimated cost (about $0.00012). You do not need to map a provider yourself: Pydantic AI's spans already say `openai`, and Opik prices them on its own.

Then open Test suites and the suite of the same name, and from there the experiment `listing-extraction-gpt-4o-mini`. It lists the 6 items with 18 runs. In our run the suite reported 1 of 6 items passing (16.7%); an earlier run of the same code passed 2 of 6, so expect your number to move. The item that never passes is the euro post: "asking 180 EUR" comes back as `price_usd: 180.0`, which fails the suite rule "price_usd is only set when the post gives a price in US dollars", and the agent also fills `location` with the shipping region. The "little Kestrel, I think bayonet" post fails too, with an invented model and condition. The "grandad's old camera" post, where every field should be null, is the one that passes.

The terminal shows the same story before the suite even runs, e.g. `price-in-euros  invented=['price_usd', 'location']`.

## Run it yourself

1. Put `OPENAI_API_KEY` in a `.env` (copy `.env.example`, or use a repo-root `.env`; the app walks up to find it).
2. Point the app at Opik. Self-hosted: set `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`. Opik Cloud: set `OPIK_API_KEY` too and `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`.
3. `uv sync`
4. `uv run main.py` (about a minute; the agent costs a fraction of a cent, the judge a few cents more).
5. Offline tests, no keys, no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Remove "Never guess" from `SYSTEM_PROMPT` and run again: watch the invented-field list grow and the pass rate drop.
- Try `gpt-4.1-mini` (change `MODEL_NAME`) and compare the two experiments on the same suite.
- Add a post of your own with one assertion per field you care about. Suite inserts de-duplicate, so only the new item is added.
- Change `runs_per_item` to 1 and see how much a single noisy run changes the verdict.

## Gotchas we hit

**Symptom:** `RuntimeError: <asyncio.locks.Event ...> is bound to a different event loop` while the suite runs.
**Cause:** `agent.run_sync` called from `run_tests`' worker threads reuses a cached HTTP client created on another thread's event loop.
**Fix:** build a fresh client per call, as `extract_listing` does: `OpenAIChatModel(name, provider=OpenAIProvider(openai_client=AsyncOpenAI()))` passed as `agent.run_sync(text, model=model)`.

**Symptom:** you edit `GLOBAL_ASSERTIONS` or the execution policy and the next run behaves as before.
**Cause:** `get_or_create_test_suite` applies those arguments only when it creates the suite.
**Fix:** change an existing suite with `suite.update(...)`, or give the suite a new name.

## How it's put together

- `listing_agent.py`: schema, agent, `check_mount` tool and the traced `extract_listing`.
- `tracing.py`: OTLP endpoint, headers, logfire and `OpikSpanProcessor` setup.
- `checks.py`: `invented_fields` / `missed_fields`, plain-Python scoring against the known values.
- `main.py`: extraction pass, test suite, judge run, flush.
- `data/posts.json`: the six posts, their true values and per-item assertions.
- `tests/test_app.py`: offline tests: corpus shape, scoring functions, the tool, and a traced call under a stub model with tracking disabled.

---
*built with Opik · inspired by Opik's examples and documentation*
