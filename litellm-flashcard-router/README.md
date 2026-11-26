# litellm-flashcard-router

*Same eight vocabulary words, two providers, one cost-and-latency table.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)

You are building a flashcard feature for a language-learning app and have two cheap candidates: OpenAI's `gpt-4o-mini` and Anthropic's `claude-haiku-4-5`. Both can fill in a card, so which one should you ship? Quality is a matter of taste, but cost and latency are numbers, and they are only useful if you collect them the same way for both providers. This example does that: one script, one LiteLLM call shape, one Opik project, one table.

## What you'll build

A small generator that reads `data/vocab.json` (eight fictional Portuguese words, each with a context sentence) and asks each model for a flashcard as a fixed JSON object: `front`, `back`, `example`, `mnemonic`. Replies are parsed and checked against that shape. LiteLLM's `OpikLogger` callback records every call, and each (model, word) pair becomes its own trace. At the end the script prints a comparison table, and `check_opik.py` rebuilds the same table from what Opik stored.

## See it in Opik

Open the `litellm-flashcard-router` project. In the Traces tab you will find 16 traces named `make_card`, eight tagged `gpt-4o-mini` and eight tagged `claude-haiku-4-5-20251001`, each with a `valid_card` feedback score (1.0 when the reply parsed into the four-field shape). Expand any trace: the `make_card` general span has one child, an llm span named like `gpt-4o-mini-2024-07-18_chat.completion_...`, with provider, token usage and an estimated cost. Switch to the Spans tab and filter by type `llm` to see all 16 llm spans together; sort by estimated cost or duration and the two models separate immediately.

In our run, the table the script printed was:

```
Model                         Valid  Tokens  Total cost     $/card  vs cheapest  Mean latency
gpt-4o-mini                     8/8    1377 $  0.000418 $ 0.000052         1.0x         1.61s
claude-haiku-4-5-20251001       8/8    1627 $  0.004211 $ 0.000526        10.1x         1.41s
```

Haiku was about ten times more expensive per card for the same eight words, and about 0.2 s faster on average. Both models returned valid cards every time, so on this workload the choice is purely cost versus speed. Every one of the 16 llm spans had a non-null cost.

## Run it yourself

1. Put `OPIK_*` settings and your `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in a `.env` (see `.env.example`); the script walks up from this folder to find one.
2. `uv sync`
3. `uv run main.py` (about 30 seconds, roughly half a cent in API spend)
4. `uv run check_opik.py` to print the per-model table computed from the llm spans in Opik; it exits non-zero if any span lacks a cost.

Offline tests: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Add a third model string to `MODELS` in `main.py` (for example another provider LiteLLM supports) and re-run; the table and the Opik tags gain a row with no other change.
- Edit `data/vocab.json` with longer context sentences and watch token counts, and therefore cost, grow for both models.
- Tighten the system prompt in `flashcards.py` ("`back` under 5 words") and compare token totals before and after.
- In Opik, filter traces by `valid_card < 1` after loosening the prompt so a model returns prose; the failing replies are one click away.

## Gotchas we hit

**An ugly "OpikLogger - Asynchronous processing not initialized ... no running event loop" traceback on startup.**
Cause: `OpikLogger()` tries to schedule a periodic flush with `asyncio`, and a plain script has no running loop. It then falls back to synchronous sending, so nothing is lost. Fix: silence just that noise while constructing the callback:

```python
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
litellm.callbacks = [OpikLogger()]
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
```

**llm spans show up as separate top-level traces instead of children of `make_card`.**
Cause: when you call `litellm.completion` inside an `@opik.track` function, the callback cannot see the surrounding span. Fix: hand it over in the call metadata:

```python
metadata={"opik": {"current_span_data": opik_context.get_current_span_data()}}
```

**The script exits before the last traces appear in Opik.**
Cause: spans are shipped from a background thread. Fix: call `opik.flush_tracker()` before exit (done at the end of `main()`).

## How it's put together

- `main.py` - loads keys, pins the project name, registers `OpikLogger`, loops models over words, prints the table.
- `flashcards.py` - system prompt, message builder, and the JSON parser/validator.
- `report.py` - turns per-call results into per-model rows and formats the table.
- `check_opik.py` - reads llm spans back from Opik and prints the same table, failing on null cost.
- `data/vocab.json` - eight fictional Portuguese words with context sentences.
- `tests/` - offline tests for parsing, table math, span grouping, and a traced call with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
