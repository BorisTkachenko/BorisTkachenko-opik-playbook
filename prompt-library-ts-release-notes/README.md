<div align="center">

# prompt-library-ts-release-notes

**Edit a prompt like code: immutable versions in Opik, and one test suite that scores v1 at 0% and v2 at 100%.**

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Opik SDK](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)
![OpenAI](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
![Tests](https://img.shields.io/badge/tests-vitest-6E9F18?style=flat&logo=vitest&logoColor=white)

</div>

When a release goes out, someone has to turn a pile of changelog bullets into a headline people will actually read. Teams hand that job to an LLM, tweak the prompt until it "sounds right", and paste the new wording into the codebase. A month later the notes are full of rocket emoji and nobody can say which wording was live, or whether the last edit made anything better.

This example keeps the prompt out of the code. It lives in Opik's **prompt library**, where every edit is an immutable, numbered version with a diff. A **test suite** with written-down rules runs against each version, so "better" becomes a pass rate, and every run is linked back to the exact version it tested.

## What you'll build

A TypeScript command-line app that writes a one-line headline and a short summary for release notes of **tidepool**, a made-up open-source file-sync CLI. Five fictional change lists (versions 3.4.0 to 4.0.0) live in `data/changelogs.json`.

- Prompt `release-note-headline`, registered twice. **v1** says "make it exciting and energetic". **v2** adds three rules: no emoji or exclamation marks, a headline that names the concrete change (the real command, flag or number), and a summary of at most two sentences.
- A test suite, `release-note-headline-rules`, holding the five change lists and those same three rules as plain-language assertions that an LLM judge checks.
- Two runs of the suite, one per prompt version, so you can compare 0% against 100% side by side.

Models: `gpt-4o-mini` writes the notes, `gpt-4.1-mini` judges them. A whole run costs about two US cents.

## See it in Opik

Open the local Opik UI (`http://localhost:5173` on the stack this example was built against) and look for four things.

**1. Prompt library, `release-note-headline`.** It has two versions, v1 and v2, each with an 8-character commit hash and a change description ("Initial version: ..." and "Add three rules: ..."). Select both versions to see the diff: v2 turns a short "be exciting" brief into one with a `Rules, all mandatory` block. Neither version can be edited afterwards; the next edit would become v3.

**2. The test suite and its two runs.** In the project `prompt-library-ts-release-notes`, open the test suite `release-note-headline-rules`. It lists two runs:

| Run | Linked prompt | Items passed | Per-assertion average |
|---|---|---|---|
| `release-note-headline-v1` | `release-note-headline` v1 | 0 of 5 (0%) | 0.00 / 0.00 / 0.00 |
| `release-note-headline-v2` | `release-note-headline` v2 | 5 of 5 (100%) | 1.00 / 1.00 / 0.93 |

Under v1 every reply breaks all three rules: it opens with a rocket or a wave emoji, shouts with exclamation marks, and spends three or four sentences on "get ready to upgrade today". Under v2 the same five inputs come back as plain text like ``Headline: `tidepool sync` is 3x faster on repositories above 10,000 files``. Open either run and the prompt version is shown on it, so the result stays meaningful after everyone forgets what "the old prompt" said.

**3. Why 5 of 5 with a 0.93 average.** The suite uses an execution policy of 3 runs per item, passing when 2 of 3 pass. The judge occasionally disagrees with itself on "at most 2 sentences" (0.93 means 1 of the 15 judgments), and the policy absorbs that without hiding it.

**4. Traces in the project.** There are 31 traces: one from the demo call, plus 30 from the suite (2 versions x 5 items x 3 runs). Open a suite trace (`evaluation_task`) and the tree reads: `llm_task` > `write-release-note` > `OpenAI.chat` for the writer, next to `metrics_calculation` > `llm_judge` > `model.generateText` for the judge. `OpenAI.chat` shows `gpt-4o-mini`, token usage and an estimated cost; the judge span is typed `llm`. The trace metadata carries `prompt_name`, `prompt_version`, `prompt_commit` and the SDK's own prompt link, so any reply can be traced to its wording.

## Run it yourself

You need Node 20+, an OpenAI key and a reachable Opik (local or Comet Cloud).

1. `cd prompt-library-ts-release-notes`
2. `cp .env.example .env` and fill in `OPENAI_API_KEY` plus your Opik settings (`OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` for a local stack, or `OPIK_API_KEY` for Comet Cloud). A `.env` in any parent folder is picked up too.
3. `npm install`
4. `npm run demo` registers v1 and v2, writes one traced note, builds the suite and runs it once per version (about 30 seconds). It ends with a comparison table and a link per run.
5. `npm run verify` reads everything back through the SDK: trace and span counts, cost, prompt versions, suite runs and the prompt linked to each. Pass an ISO timestamp (`npm run verify -- 2026-11-26T09:00:00Z`) to ignore older runs.
6. `OPIK_TRACK_DISABLE=true npm test` runs the offline tests (no keys, no Opik).

Running `npm run demo` again is safe for the library and the suite: a prompt version that already exists is skipped, and the suite is only seeded when empty. It does add another pair of runs.

## Poke around

- Add a third version to `src/prompts.ts` (say, "end the summary with an upgrade command") and register it in `src/library.ts`. The library gains a v3 and the diff view lets you compare any two versions.
- Remove the sentence rule from v2 and re-run the suite. Watch which assertion drops while the other two stay at 1.00; the per-assertion averages tell you which rule was carrying the pass rate.
- Set `runsPerItem: 1, passThreshold: 1` in `src/suite.ts` and re-run a few times to see how much one judgment can move the pass rate.
- Add a sixth change list to `data/changelogs.json` that is only a security fix and see whether "names a concrete change" still holds.

## Gotchas we hit

**`npm install opik-openai` fails with `ERESOLVE ... peer opik@"^1.8.61" from opik-openai@2.3.4`.** The integration declares a peer range for the 1.x Opik SDK, but the current SDK is 2.x. Tell npm the two belong together with an override in `package.json`:

```json
"overrides": { "opik-openai": { "opik": "$opik" } }
```

**The prompt versions have no change description even though you passed `changeDescription`.** In opik 2.3.4 `client.createPrompt({ changeDescription })` accepts the option but never sends it, so `getVersions()` returns `undefined` for it. Create versions through the REST client instead, which stores it:

```ts
await client.api.prompts.createPromptVersion({
  name, projectName, templateStructure: "text",
  version: { template, type: "mustache", changeDescription },
});
```

`createPrompt` also only compares against the latest version, so a loop that re-registers v1 after v2 would append a duplicate. `src/library.ts` looks the version up first and skips it when the text matches.

**Every OpenAI call shows up as its own one-span trace named `OpenAI.chat`, next to your tracked function.** `trackOpenAI` does not read the context of `track()`; it opens a new trace unless you hand it a parent. Pass the active span (and note that this wrapper logs the call as a `general` span with model, usage and cost, not an `llm` span):

```ts
trackOpenAI(new OpenAI(), { client: opik, parent: getTrackContext()!.span })
```

**The v2 run reports 80% instead of 100% with a small judge.** With `gpt-4o-mini` as the judge, 3 of 15 "at most 2 sentences" verdicts were wrong on replies that had exactly two, which failed one item. Use a stronger judge model (`model: "gpt-4.1-mini"` in `runTests`, and leave `reasoning_effort` out of any judge override) and keep the execution policy of 3 runs per item. The AI SDK warning about system messages that prints once per judge call is harmless.

## How it's put together

- `src/main.ts`: the demo. Registers prompts, makes one traced call, builds the suite, runs it per version and prints the comparison.
- `src/config.ts`: project name, suite name, and `OPIK_PROJECT_NAME`, which must be set before anything imports `opik`.
- `src/library.ts`: pushes v1 and v2 to the prompt library, skipping versions that already exist.
- `src/prompts.ts`: the two prompt texts and their change descriptions.
- `src/traced.ts`: `write-release-note`, the `track()`-wrapped function that fetches a pinned prompt version and calls the OpenAI client wrapped by `opik-openai`.
- `src/suite.ts`: the three assertions, the execution policy and the five suite items.
- `src/writer.ts`: the plain OpenAI call, with no Opik code in it.
- `src/changelogs.ts`, `src/env.ts`: load the fictional data and the nearest `.env`.
- `src/rules.ts`: local, deterministic versions of the three rules (used by the unit tests, not by the suite).
- `src/verify.ts`: reads the results back from Opik.
- `data/changelogs.json`: five fictional tidepool change lists.
- `tests/rules.test.ts`: rule checks, data loading and prompt contents.
- `tests/traced.test.ts`: calls the `track()`-wrapped writer with tracking disabled and a stubbed client, to show the wrapper does not get in the way of unit tests.

---

*built with Opik · inspired by Opik's examples and documentation*
