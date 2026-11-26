<div align="center">

# 🥣 Read the Label, Check the Label

**`openai-vision-nutrition-labels`**

*A small installable package that turns nutrition-facts photos into typed fields, and shows you the photo next to every answer.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/openai-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

</div>

---

A vision model that misreads `85 mg` as `65 mg` leaves no clue in a text log.
The input was pixels, and the log only has a base64 blob. This example extracts
ten fields (product name, serving size, servings per container, calories, fat,
sodium, carbs, sugars, protein, allergens) from nutrition-facts labels, attaches
each label PNG to its Opik trace, and runs an Opik test suite that states the
correct value of every field. Some labels are made hard on purpose, so the suite
reports real failures instead of a flattering 100%.

## What you'll build

An installable package, `nutrilabel`, with a `nutrilabel` command:

- `nutrilabel render` draws eight label PNGs with Pillow from the fictional
  products in `data/products.json`. Nothing binary is committed. Four are
  deliberately hard: a **smudged** middle band, a label **rotated** 17 degrees,
  **tiny print** on a shrunken label, and one whose **sodium line is missing**
  (the right answer is `null`).
- `nutrilabel extract` sends each label to `gpt-4o-mini` with a strict JSON schema
  and prints the typed record.
- `nutrilabel suite` builds an Opik test suite (global format rules plus four
  per-label assertions holding the expected values), runs every label through
  extraction, and has an LLM judge grade each assertion.

## See it in Opik

Open the project **`openai-vision-nutrition-labels`** at `http://localhost:5173`
(or your own Opik). After the suite run it holds eight traces named
`evaluation_task`, one per label. Open one: the **Attachments** tab shows the label PNG
the model actually received (`oat-crunch.png`, `trail-mix-smudged.png`, ...), and
the trace tree contains an `extract_label` span with a `chat_completion_create` llm
span inside it. That span carries about 26,000 tokens for a full-size label (the image
is most of them) and roughly `$0.0024`. The shrunken `pasta-tiny.png` is cheaper:
8,973 tokens, `$0.0011`. In the same tree you will see the judge's `completion` spans.
`nutrilabel extract` on its own produces plain `extract_label` traces with the same
attachment.

Then open **Test suites** and the experiment `nutrition-labels-gpt-4o-mini`. In the
run behind these numbers 7 of 8 labels passed. The failure is
`trail-mix-smudged.png`: the model returned fat `13`, sodium `65` and carbs `19`
where the label says `12`, `85` and `17`. The smudged band is half legible and the
model fills the blur with plausible digits. What passed is just as interesting: the
rotated label, the tiny print, and `kefir-no-sodium.png`, where the model correctly
returned `sodium_mg: null` instead of inventing a number. Model output varies a little
from run to run, so expect the smudged label to fail and the others to mostly pass,
not these exact digits.

## Run it yourself

1. Install: `uv sync`
2. Put your key in a `.env` (here or in any parent folder), based on `.env.example`:
   `OPENAI_API_KEY=...`. Point Opik at your server with `opik configure`, or set
   `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` in the same file.
3. Draw the labels: `uv run nutrilabel render`
4. Extract fields (optional, one trace per label): `uv run nutrilabel extract`
5. Run the test suite: `uv run nutrilabel suite` (about a minute, a few cents)

Tests run offline: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.
`OPIK_TRACK_DISABLE=true` turns Opik tracking into a no-op.

## Poke around

- Edit the `smudge` style in `data/products.json` (or `GaussianBlur` in
  `render.py`) and watch the pass rate move.
- Add a ninth product in the JSON; the suite and renderer pick it up with no code change.
- Swap `MODEL` in `config.py` for `gpt-4.1-mini` and compare the two experiments.
- Remove the `Attachment(...)` line in `extract.py` and look at the trace again: you
  are back to a base64 string.

## Gotchas we hit

**The suite still shows my old items and assertions after I edited them.**
`get_or_create_test_suite` returns an existing suite unchanged and `insert` adds new
items next to the old ones; after editing one assertion the next run reported
"12/16 labels". Sync explicitly:

```python
suite.update_test_settings(global_assertions=GLOBAL_ASSERTIONS)
suite.clear()
suite.insert(build_items())
```

**A clean label fails with correct output.** The first assertion said allergens are
"exactly: peanuts, soy, milk" while the extractor returned them sorted
(`milk, peanuts, soy`); the judge took the order literally and failed two labels.
Write set-like expectations as "in any order and with no extras".

**Cost looks high for a tiny label.** `detail: "high"` tiles the image, so a 520x640
label costs about 26,000 tokens on `gpt-4o-mini`. Use `"low"` if the print is large.

## How it's put together

- `pyproject.toml`: hatchling package, `nutrilabel` console script, pinned `opik>=2.2.89`.
- `data/products.json`: eight fictional products and their `style` flags for the hard cases.
- `src/nutrilabel/config.py`: project name, model, `.env` loading, `OPIK_PROJECT_NAME`.
- `src/nutrilabel/schema.py`: `NutritionFacts`, the strict nullable JSON schema, `parse_facts`.
- `src/nutrilabel/render.py`: Pillow drawing, smudge, rotation, tiny print, omitted lines.
- `src/nutrilabel/extract.py`: `track_openai` client and the `@opik.track` function that attaches the PNG.
- `src/nutrilabel/suite.py`: global assertions, per-label assertions, `run_tests`.
- `src/nutrilabel/cli.py`: the `render` / `extract` / `suite` subcommands.
- `tests/test_nutrilabel.py`: rendering, parsing, assertions and a traced call with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
