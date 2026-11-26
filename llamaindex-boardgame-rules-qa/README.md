<div align="center">

# Rules Lawyer for the Game Shelf

**`llamaindex-boardgame-rules-qa`**

*Settle table arguments from the rulebook, and prove the ruling is the right one.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/llama--index-0.14-6a4c93?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

</div>

---

Nobody reads the rulebook until two players disagree about it. A rules bot has to be
exact: "a hand limit of 7" and "a hand limit of 8" are different games, and a bot that
quietly imports a rule from the *other* game on the shelf is worse than no bot. This
project answers rules questions over three fictional rulebooks (Lanternfall, Saltmarsh
Couriers, Quillfire Duel) with LlamaIndex, traces every question in Opik so you can see
what retrieval handed the model, and runs a rule-level test suite that asks whether each
answer states the right rule and cites the right game and section.

## What you'll build

- `rulebook/corpus/` holds the rulebooks as plain Python data and renders them to PDFs
  with reportlab. The three small PDFs in `data/pdfs/` are committed, and are regenerated
  automatically if missing, so a fresh clone runs as-is.
- `rulebook/index/` reads the PDFs with LlamaIndex's file reader and persists a vector
  index (OpenAI `text-embedding-3-small`) to `storage/`.
- `rulebook/qa/` is a query engine with a "strict rules lawyer" prompt that forces a
  `[Game, Section N]` citation, answered by `gpt-4o-mini`.
- `rulebook/suite/` defines 8 rule cases and runs them with `opik.run_tests`.
- `rulebook/cli.py` ties it together: `rulebook build`, `rulebook ask`, `rulebook suite`.

## See it in Opik

Open the project **llamaindex-boardgame-rules-qa**. After the full run it holds 28
traces: 4 named `query` from `rulebook ask`, and 24 named `evaluation_task` from the
suite (8 items, each run 3 times).

Open any `query` trace, for example "Two Lanternfall players tie on points. Who wins?".
Its tree is `retrieve` (with an `embedding` child) followed by `synthesize`, whose
children are two `chunking` spans, a `templating` span and an `llm` span. The
`retrieve` output is the four rulebook chunks that were fetched; the `llm` span shows the
full prompt with those chunks pasted in, the model (`gpt-4o-mini-2024-07-18`), token usage
and an estimated cost. When a ruling is wrong, this tree tells you whether retrieval
fetched the wrong section or the model misread the right one.

Then go to **Experiments** and open the latest `boardgame-rules-suite` run. It scored
**7 of 8 items passing** (pass threshold: 2 of 3 runs). Every item shows the assertions
the judge checked, including "The answer cites Lanternfall, Section 3". The one failure
is instructive: asked "What is the hand limit in Lanternfall?", the bot said the
rulebooks do not cover it, but the judge noted that the retrieved Lanternfall excerpt
says to refill your hand to 5 tiles, so "no hand limit" is arguable. That is a real
ambiguity in the rulebook (and in the assertion), not a crash; the CLI prints the judge's
reasons for every failed run. Each suite run also left the full `retrieve`/`synthesize`
tree under its `evaluation_task` trace, so a failing row jumps straight to the chunks.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or use a repo-root `.env`; the app
   walks up to find one). Opik needs a running instance, local or cloud.
2. `uv sync`
3. `uv run rulebook build` indexes the PDFs into `storage/`.
4. `uv run rulebook ask` answers four demo questions; `uv run rulebook ask "your question"` answers one.
5. `uv run rulebook suite` creates the `boardgame-rules-suite` test suite and runs it.
   It prints a pass rate, per-item results and citation checks, and the experiment URL.
6. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

A full run takes about 2 minutes and costs a few cents.

## Poke around

- Add a fourth rulebook to `corpus/games.py`, run `build`, and add a case to
  `suite/items.py`. Does the bot start mixing the new game's rules into old answers?
- Change `similarity_top_k` in `qa/engine.py` from 4 to 1 and re-run the suite. Which
  cross-section questions break, and does the trace show the missing chunk?
- Rewrite the hand-limit assertion so it matches what the rulebook actually says, and
  see whether the item flips to passing.
- Raise `runs_per_item` in `suite/run.py` to 5 and watch which items are flaky.

## Gotchas we hit

**`ValueError: No files found in .../data/pdfs` although the PDFs are there.**
`SimpleDirectoryReader` skips hidden files and also treats any path containing a dot
folder (a checkout under `~/.worktrees/`, for instance) as hidden. Pass
`SimpleDirectoryReader(dir, required_exts=[".pdf"], exclude_hidden=False)`.

**Reading PDFs fails with an import error.** The `llama-index` meta-package no longer
bundles file readers. Add `llama-index-readers-file` to your dependencies.

**Edited assertions or the execution policy do not change in Opik.**
`get_or_create_test_suite` ignores new settings for a suite that already exists. Call
`suite.update_test_settings(global_assertions=..., global_execution_policy=...)` after it,
as `suite/run.py` does.

**Judge flakiness.** A single LLM-judge run per item flips on borderline wording. Use
an execution policy (`{"runs_per_item": 3, "pass_threshold": 2}`) rather than a
`reasoning_effort` override on the judge model, which the judge rejects.

## How it's put together

- `rulebook/config.py`: paths, model names, `.env` discovery.
- `rulebook/tracing.py`: installs Opik's `LlamaIndexCallbackHandler` and flushes.
- `rulebook/corpus/games.py`: the three fictional rulebooks as data.
- `rulebook/corpus/pdfs.py`: renders them to PDF, regenerating missing ones.
- `rulebook/index/build.py`: reads the PDFs, builds, persists and loads the index.
- `rulebook/qa/engine.py`: the cited-ruling prompt and `ask()`.
- `rulebook/suite/items.py`: the 8 rule cases and global assertions.
- `rulebook/suite/checks.py`: deterministic citation parser.
- `rulebook/suite/run.py`: suite sync and `run_tests` task.
- `rulebook/cli.py`: the `build`, `ask`, `suite` subcommands.
- `tests/test_rulebook.py`: offline tests for PDFs, citation checks, case validity, a stub engine, and a traced call with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
