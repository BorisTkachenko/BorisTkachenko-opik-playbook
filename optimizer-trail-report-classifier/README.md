# optimizer-trail-report-classifier

*A ranger-desk prompt that does fine on easy reports, an optimizer that learns the desk's edge-case rules, and a held-out check that decides whether the rewrite is allowed into the prompt library.*

[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat)](pyproject.toml)
[![opik](https://img.shields.io/badge/opik-2.3.4-2e8555?style=flat)](https://github.com/comet-ml/opik)
[![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2.0-orange?style=flat)](https://github.com/comet-ml/opik)

Visitors to Ridgeback Hollow National Park (a made-up place) file short trail reports: a fallen spruce, a moose at Tern Pond, a lost key fob, a thank-you note. The rangers route each one to a team, and a first-draft prompt gets the obvious reports right and the awkward ones wrong. A stray dog is not wildlife, a cougar sighting is not a nature note, and "is the road plowed yet?" is not a hazard. Editing the prompt by hand gives you no way to tell a real gain from a lucky afternoon. This example measures it: score the draft, let Opik's Agent Optimizer rewrite it under a fixed budget, then test the winner on reports the optimizer never saw.

## What you'll build

A small `trailclass` package with a three-command CLI, one command per stage:

| command | what it does |
|---|---|
| `baseline` | uploads two datasets (49 training reports, 32 held-out validation reports), saves the hand-written prompt as the first version in the Opik prompt library, and scores it on both splits as experiments |
| `optimize` | runs a HierarchicalReflectiveOptimizer for at most 10 trials on the training split only, gpt-4o-mini doing both the classifying and the reasoning |
| `publish` | scores baseline and winner on the validation split, and saves the winner as a new prompt-library version only if it is a different prompt that beats the baseline there by at least 0.08 |

The model's reply is constrained to the six categories with a JSON-schema enum (`trail_hazard`, `wildlife_sighting`, `facility_issue`, `lost_and_found`, `compliment`, `other`), so every prompt produces a valid label and the optimizer can only improve *which* category is picked, never how the answer is worded.

The baseline fails for a reason you can read in `trailclass/prompts.py`: each category has a one-line gloss that is fine for easy reports and wrong for the edge cases. The desk's real conventions, which only the labelled data carries, are:

- any animal that blocks, charges or follows people, and any sighting of a large predator (bear, cougar, wolf, coyote), is a `trail_hazard`; harmless animals merely seen are `wildlife_sighting`
- lost, stray or unattended pets are `lost_and_found`
- damaged amenities (railings, benches, signs), litter, graffiti and vandalism are `facility_issue`
- questions about conditions or hours, suggestions, and complaints about other visitors are `other`

About a third of the training reports and a third of the validation reports are edge cases of this kind.

## See it in Opik

Everything lives in the project **optimizer-trail-report-classifier**. The numbers below come from one clean run of the three commands; yours will differ, because gpt-4o-mini is not deterministic and the optimizer follows whatever failures it happens to see.

- **Optimization runs**, newest run, dataset `ranger-desk-train`. The score curve across trials: seven experiments scoring 0.735 (the starting prompt), 0.714, 0.816, 0.878, 0.878, 0.898 and 0.959. The optimizer stopped after 5 trials of its 10-trial budget because the curve had flattened. Click a trial to read the exact system prompt it tried and the per-report results, including the `reason` string the metric returns ("predicted wildlife_sighting, expected trail_hazard"), which is what the reflective optimizer reads to decide what to fix. `optimize` prints a link pinned to the project (see Gotchas).
- **Experiments**, filter to dataset `ranger-desk-validation`: `baseline-validation` (0.594), `baseline-validation-recheck` (0.594) and `winner-validation` (0.750). Select the recheck and the winner and open compare to see which individual reports flipped. The metric column is `category_match`. `baseline-train` (0.714) sits on the training dataset.
- **Prompt library > `trail-report-classifier`**. Two versions: the hand-written baseline (`source: hand-written baseline`) and the optimizer's winner, whose metadata reads `train_accuracy: 0.735 -> 0.959` and `validation_accuracy: 0.594 -> 0.750`. Winners from other runs carried the same idea in different words: "wildlife that may pose a risk goes to trail_hazard", plus a nudge toward facility problems.
- **Traces**: 499 traces in the project, each with an `llm` span (gpt-4o-mini, token usage and estimated cost): `evaluation_task` traces for every report scored (each holding a `classify_report` span with the llm span beneath it) and `optimizer_llm_call` traces for the optimizer's reasoning. The whole run cost about $0.02, summed from `total_estimated_cost` on the llm spans.

It repeats: two earlier complete runs of the same code improved validation from 0.625 to 0.812 (+0.188) and from 0.625 to 0.781 (+0.156).

Budget matters. In earlier trials of this design with 6 trials instead of 10, one run improved validation by only 0.06 and `publish` correctly saved nothing: when the optimizer finds no clear gain, the library stays untouched.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or keep it in a `.env` further up the tree; the app walks up to find one). Point the Opik SDK at your instance as usual (`opik configure`, or `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE`).
2. `uv sync`
3. `uv run python -m trailclass baseline`
4. `uv run python -m trailclass optimize` (1 to 2 minutes)
5. `uv run python -m trailclass publish`
6. Open Optimization runs in Opik and follow the printed link.

Re-running `baseline` saves another identical baseline version in the library. Offline tests, no keys and no Opik needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Set `MAX_TRIALS = 4` in `trailclass/config.py`, run the sequence a few times, and count how often `publish` refuses to save.
- Add your own edge-case reports to `data/train.jsonl` (say, a drone complaint labelled `other`) and see whether the optimizer picks the rule up.
- Lower `MIN_GAIN` in `trailclass/publish.py` to 0 and watch lateral moves slip into the library.
- Swap `HierarchicalReflectiveOptimizer` for `MetaPromptOptimizer` in `trailclass/optimize.py` and compare the trial curves (see the second Gotcha).

## Gotchas we hit

**Every candidate scores 0.0 and the "winner" is the baseline.** With free-text answers and an exact-match metric, optimizer rewrites paraphrased the labels ("trail hazard, lost and found") and every reply failed to match. The prompt is then being graded on wording, not judgment. Constrain the reply instead of hoping the prompt stays strict: `response_format={"type": "json_schema", "json_schema": {..., "schema": {"properties": {"category": {"enum": [...]}}}}}`, passed both to the app's client (`trailclass/classify.py`) and to the optimizer through `ChatPrompt(model_kwargs={"response_format": ...})`. The metric then reads `category` out of the JSON (`extract_label`).

**The optimizer runs all its trials and never beats the baseline.** With the enum in place, `MetaPromptOptimizer` (6 trials, three candidates per round) kept producing paraphrases that scored at or below the starting prompt, because the numeric score alone does not say *which* reports failed. `HierarchicalReflectiveOptimizer` plus a metric that returns a `ScoreResult` with a reason (`predicted X, expected Y`) found the desk's rules in 2 of 2 final runs; the reason strings are in `trail_report_accuracy`.

**The prompt version in the library has no change description.** `create_chat_prompt(..., change_description="...")` runs without error, but reading the version back returns `None` on the stack and SDK versions pinned here, while `metadata` round-trips. Put the story there instead: `client.create_chat_prompt(name=..., messages=..., metadata={"validation_accuracy": "0.625 -> 0.812"})`.

**The winning system prompt can contain a literal `{report}`.** The optimizer sometimes pastes the user-message placeholder into the system text. Saved as-is it ships to the library (and gets scored) with the stray token. `trailclass/optimize.py` strips it first: `re.sub(r"[:\s]*\{report\}", "", system)`.

**`get_run_link()` can open an empty-looking run.** The SDK result's link goes through `/v1/session/redirect/optimizations/` and lands on `/<workspace>/optimizations/<dataset_id>/compare`, a URL with no project in it, so the page is resolved against whichever project the UI last had active. `optimize` builds a project-scoped URL instead (`.../projects/<project_id>/optimizations/<optimization_id>`, see `trailclass/links.py`), taking the project id from `rest_client.optimizations.get_optimization_by_id`.

## How it's put together

- `trailclass/cli.py`: the `baseline`, `optimize` and `publish` subcommands, the Opik client, and the flush in `finally`.
- `trailclass/config.py`: project name, models, labels, the enum response format, trial budget, dataset and prompt names; sets the Opik project before anything is imported.
- `trailclass/data.py`: loads and validates `data/train.jsonl` and `data/validation.jsonl`.
- `trailclass/prompts.py`: the hand-written starting prompt.
- `trailclass/classify.py`: the traced classifier (`track_openai` client plus `@opik.track`).
- `trailclass/metric.py`: label extraction, the optimizer metric (score plus reason) and the Opik scoring metric `category_match`.
- `trailclass/experiments.py`: runs a prompt over a dataset as an Opik experiment.
- `trailclass/optimize.py`: the bounded optimizer run, placeholder cleanup, hand-off to `publish` via `.state/winner.json`.
- `trailclass/publish.py`: the held-out gate.
- `trailclass/opik_assets.py`: dataset upload and prompt-library saves.
- `trailclass/links.py`: the project-pinned optimization link.
- `data/`: 49 training and 32 validation reports, all fictional.
- `tests/`: dataset and label-extraction checks, a traced `classify` call with tracking disabled and a stubbed client, the placeholder cleanup and the publish gate.

---

*built with Opik · inspired by Opik's examples and documentation*
