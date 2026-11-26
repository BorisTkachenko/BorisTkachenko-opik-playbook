<div align="center">

# Museum Audio Guide with Verbatim Citations

**`anthropic-ts-museum-guide-citations`**

*An audio guide that must quote the placards it answers from, and an Opik test suite that checks every quote.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Anthropic SDK](https://img.shields.io/badge/%40anthropic--ai%2Fsdk-1.14-191919?style=flat)
[![Opik](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)](https://github.com/comet-ml/opik)
![Tests](https://img.shields.io/badge/vitest-9%20offline%20tests-6E9F18?style=flat&logo=vitest&logoColor=white)

</div>

---

A visitor asks the audio guide how many prisms the great lens has. A confident, wrong
answer is worse than none: nobody at the museum can tell it was invented. This example
builds a guide for a fictional lighthouse museum (the Pellwick Lamp Museum) that answers
only from its placards, quotes them word for word, and says "I don't know" when the
placards are silent. Then it turns those expectations into a **test suite**: plain-English
assertions, graded pass or fail for every question, viewed as one run in Opik.

## What you'll build

- A TypeScript guide on the Anthropic SDK (Claude Haiku 4.5). Its system prompt holds six
  short galleries of exhibit notes (`docs/`) and requires every claim to carry a
  `<quote>…</quote>` copied from the notes.
- Hand-written Opik tracing. Opik has no first-party TypeScript integration for the
  Anthropic SDK, so the code opens the traces and the `llm` span itself (model, provider
  `anthropic`, token usage), and Opik prices the call from that.
- A test suite of seven visitor questions with three suite-wide assertions and
  question-specific ones. Four of the seven are traps: two are not in the notes at all
  (a cafe, the tower's architect), one has a false premise ("why was the lens made in
  Paris?"; the notes say Lille), one needs a negative answer (open on Tuesday? no).
- A deterministic check (`verifyQuotes`) that does the same verbatim test in plain code,
  printed beside the judge's verdict so you can see where the two agree.

Question → guide answers with quotes → LLM judge grades each assertion, three runs per
question → pass or fail per question in one Opik suite run.

## See it in Opik

Open the project **anthropic-ts-museum-guide-citations** (same name as this folder).

**Traces.** `npm run demo` leaves three traces named `answer_question`. Open one: a general
span `answer_question` contains an `llm` span, `anthropic.messages.create`, showing model
`claude-haiku-4-5-20251001`, provider `anthropic`, about 1,775 prompt tokens (nearly all of
it the exhibit notes) and a small completion, with an estimated cost of roughly $0.002 per
call. The output is the guide's answer with its `<quote>` tags.

**Test suites.** Open the Test suites tab and then **museum-guide-citation-suite**. It holds
seven items; each stores only the question and the notes, with no expected answer, so the
judge grades against the source and not against a key. The suite's execution policy runs
each item 3 times and passes it if 2 runs pass. In the run named `guide-2026-11-26T09:12`
(the timestamp in the name is when the run started) all seven items passed, 3 of 3 runs
each, and every assertion averaged 1.0 across 21 samples.

**Inside one run.** Each sample is an `evaluation_task` trace. Its tree shows `llm_task` →
`answer_question` → `anthropic.messages.create` (the guide, about $0.0024) next to
`llm_judge` → `model.generateText` (the judge's grading of every assertion, about $0.005).
Because the guide's span sits in that tree, you can click from a failed assertion to the exact
prompt and answer that earned it.

## Run it yourself

1. Install: `npm install`
2. Provide a key: copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`, or reuse a
   `.env` at an ancestor folder (the app walks upward to find one).
3. Point at Opik. For a local stack the `.env.example` defaults work
   (`OPIK_URL_OVERRIDE=http://localhost:5173/api/`, `OPIK_WORKSPACE=default`). For Opik Cloud
   set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`, `OPIK_API_KEY`, `OPIK_WORKSPACE`.
4. Three traced questions: `npm run demo` (about 5 s, under a cent).
5. The test suite: `npm run suite` (about a minute, roughly 15 cents: 21 guide answers plus
   the judge grading them).
6. Offline tests, no keys and no Opik: `OPIK_TRACK_DISABLE=true npm test`

## Poke around

- Delete the sentence "If the notes do not cover the question, say plainly that you do not
  know" from the prompt in `src/notes.ts` and re-run the suite. Watch the cafe and architect
  items.
- Add a question whose answer is split across two galleries (the lens date and the lamp
  fuel) and see whether the guide still quotes from a single sentence.
- Tighten an item with `executionPolicy: { runsPerItem: 5, passThreshold: 5 }` to demand
  consistency.
- Switch `MODEL` in `src/guide.ts` and compare cost per call on the span.

## Gotchas we hit

**Symptom: the demo ran, but the project page is empty and the traces are in "Default Project".**
`track()` builds its own internal client from the environment; the client you create with
`new Opik({ projectName })` and `setGlobalClient()` is used for explicit calls, but not by
`track`. Fix: set the project for both.

```ts
process.env["OPIK_PROJECT_NAME"] = PROJECT_NAME;                  // read by the client behind track()
export const guide = track({ name: "answer_question", type: "general", projectName: PROJECT_NAME }, fn);
```

## How it's put together

- `docs/` six fictional galleries of placards (about 1,700 tokens in total).
- `src/notes.ts` loads the notes, builds the system prompt, extracts `<quote>` spans and verifies them.
- `src/guide.ts` the Anthropic call, with the hand-built `llm` span and the `track` wrapper.
- `src/tracing.ts` the Opik client and project name, plus the flush helper.
- `src/suite.ts` the questions, the plain-English assertions and the item builder.
- `src/evaluate.ts` creates the test suite and runs it with the judge.
- `src/main.ts` three traced demo questions; `src/questions.ts` holds them.
- `tests/` offline vitest: quote parsing and verification, the suite definition, and a traced
  call against a stubbed Anthropic client with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
