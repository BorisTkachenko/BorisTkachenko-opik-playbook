# dspy-astronomy-fact-checker

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![DSPy](https://img.shields.io/badge/DSPy-3.x-8B0000?style=flat)
![Opik SDK](https://img.shields.io/badge/Opik%20SDK-2.3.4-2f54eb?style=flat)

*A claim checker that knows the answer but not the house style, until DSPy compiles the style into its prompt.*

## The problem

Ask a model "is this claim true?" and it will happily say "The claim is false." Ask a pipeline downstream of it for one of three labels and an evidence id, and that sentence is useless. The knowledge was never missing; the convention was. Writing the convention into the prompt by hand works until the next convention. DSPy's answer is to show the program a few worked examples and let an optimizer bake them into the prompt, but you only trust that if you can measure the program before and after, on identical data, and look inside the prompt that changed.

This project does that on a small fictional case: a fact sheet about the invented Veyra star system and its Marrow Ridge Observatory. The model cannot answer from world knowledge, because none of it exists.

## What you'll build

A `dspy.ChainOfThought` program takes a claim plus the fact sheet (`data/factsheet.txt`, fourteen numbered lines `F-01` to `F-14`) and returns two fields: `verdict` and `evidence`. The house convention is that the verdict is one of `SUPPORTED`, `REFUTED`, `NOT_ENOUGH_INFO` and the evidence is the bare id of the deciding line (`F-10`), or `NONE`. The signature says none of that. Only the worked examples do.

- 12 held-out claims (4 of each label) are uploaded as an Opik dataset, `veyra-claims`.
- Three metrics score each answer: `decision_correct`, `evidence_correct`, `fully_correct`. Scoring is forgiving about typography (case, punctuation, brackets, underscores vs spaces), so it measures the decision and not whitespace, but it is strict about vocabulary: "True" is not `SUPPORTED`, and a sentence is not an id.
- `opik.evaluate` runs the uncompiled program (experiment `dspy-uncompiled`), then `dspy.BootstrapFewShot` compiles it from 8 answered claims, then the compiled program runs on the same dataset (experiment `dspy-compiled`).
- `OpikCallback` traces every DSPy call, including the compile-time teacher attempts.

## See it in Opik

Open the **`veyra-claims`** dataset's experiments (the run prints a compare link). Two experiments sit side by side. `dspy-uncompiled` scores 0.00 on all three metrics; `dspy-compiled` scores 1.00 on all three, over the same 12 claims. In two complete runs the result was identical both times: 0/12 before, 12/12 after.

The 0 is not a model that is wrong. Open any row of the uncompiled experiment and read the output: verdicts like "The claim is false." and "The claim cannot be verified.", evidence like "[F-10] Brume's atmosphere contains methane and carbon dioxide; no oxygen has been detected." or "No relevant evidence regarding the cost of the Pellam telescope is provided". Meaning right, convention missing. Each metric's `reason` shows the verdict it normalised and the gold label. In the compiled rows the same claims come back as `REFUTED` / `F-10`, `NOT_ENOUGH_INFO` / `NONE`. The experiment config records `demos: 0` versus `demos: 8`.

Now open the **`dspy-astronomy-fact-checker`** project's Traces tab. Each evaluated claim is an `evaluation_task` trace containing the `task` span, then `ChainOfThought`, `Predict`, and an llm span named `LM: openai - gpt-4o-mini` with token usage and an estimated cost (about $0.0004 for a compiled call). Open an uncompiled LM span and then a compiled one: the average prompt grows from roughly 800 to roughly 4,000 tokens, because the prompt now carries the 8 demonstrations, each with the full fact sheet. That is the price of the improvement, visible as a number. Four extra traces per run are named `ChainOfThought` rather than `evaluation_task`: those are the optimizer's teacher attempts, whose answers became the demos, and they carry the DSPy module graph in their metadata.

## Run it yourself

1. `cd dspy-astronomy-fact-checker`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or rely on a `.env` one directory up; both are read). To point at your own Opik, also set `OPIK_URL_OVERRIDE` / `OPIK_API_KEY` / `OPIK_WORKSPACE` as usual.
3. `uv sync`
4. `uv run main.py` (about one minute, around a cent of `gpt-4o-mini`)
5. Open the compare link it prints, then the `dspy-astronomy-fact-checker` project.

Offline tests, no key and no Opik needed:

`env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Loosen `normalise_verdict` to map "true"/"false" to the labels and re-run: the uncompiled decision score jumps, the evidence score does not. How much of the gap was vocabulary, how much format?
- Set `max_bootstrapped_demos=1` and `max_labeled_demos=1` in `checker.compile_program`. How few demos still teach the evidence format?
- Add a claim that two fact lines jointly decide. The convention has one id per answer, so the metric and the demos disagree with the data. What does the experiment show?
- Compare an uncompiled and a compiled `LM` span input in the trace view and find the exact demo that taught `NONE`.

## Gotchas we hit

**`evaluate()` warns: "The `project_name` parameter of `evaluate()` is deprecated".** The experiment's project now comes from the dataset. Create the dataset with `client.get_or_create_dataset(name, project_name=PROJECT_NAME)` and leave `project_name` off `evaluate()`.

**Re-running piles up duplicate dataset items.** `dataset.insert` adds rows every time. Call `dataset.clear()` before inserting so every run evaluates exactly the same 12 claims.

**The compiled score is not repeatable with a small demo budget.** With `max_labeled_demos=4`, one early run bootstrapped fewer teacher traces and the compiled decision score came out 8/12 instead of 12/12: which demos reach the prompt varies between compiles. Setting `max_labeled_demos=8` (the whole trainset) tops the prompt up to every example, and every run after that scored 12/12. When the trainset is tiny, make the labeled budget its size.

**A custom stub LM no longer works in tests on DSPy 3.5.** `dspy.BaseLM` subclasses must supply an engine, so the offline test stubs the program instead (`StubProgram` in `tests/test_checker.py`).

## How it's put together

- `checker.py`: signature, program, fact sheet and claims loading, normalisation and scoring rules, `compile_program`. No Opik code.
- `metrics.py`: the three Opik metrics, thin wrappers over `checker` that produce the per-claim score columns.
- `main.py`: wires `OpikCallback`, builds the dataset, runs both experiments, prints the comparison, flushes.
- `data/factsheet.txt`: the fictional Veyra fact sheet. `data/claims.json`: 8 training and 12 held-out claims with gold labels and evidence ids.
- `tests/test_checker.py`: normalisation, evidence strictness, data consistency, the compile metric, the Opik metrics, and a task run with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
