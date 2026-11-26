# whisper-vet-voicemail-triage

*A vet clinic's voicemail box, triaged by a model, with the recording one click away from every decision it made.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-TTS%20%2B%20Whisper%20%2B%20chat-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.3.4-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

Monday morning, the front desk has four voicemails and one pair of hands. A triage assistant listens first and sorts them: *emergency*, *same-day*, *routine*, plus a callback list of who to ring and about which pet. The cost of a mistake is lopsided. A dog that ate xylitol gum and got filed as "routine" waits behind a vaccination booking.

When the sort looks wrong, the text log is no help. What the model saw was a Whisper transcript, not the call. Did Whisper mishear, or did the model misjudge? You can only answer that by listening. And because the judge you use to test the sorter is itself a model, you also need a test setup that does not cry wolf when the judge has a bad moment.

This example wires both: a playable audio attachment on every trace, and a judge-checked test suite with a retry policy.

## What you'll build

A four-step pipeline on the OpenAI SDK, run once per voicemail:

1. **Speak**: four fictional scripts in `data/voicemails.json` are turned into MP3s with `tts-1` (one voice per caller, short clips). The audio is output, so it lands in `output/audio/`, is git-ignored, and is regenerated on every run.
2. **Transcribe**: `whisper-1` turns the MP3 back into text.
3. **Triage**: `gpt-4o-mini` returns JSON: an urgency level, a one-sentence reason, and one callback entry (owner, pet, number, reason) per pet mentioned.
4. **Queue**: `main.py` merges everything into one callback list, most urgent first.

Then `evaluate.py` replays each transcript through the triage step under an Opik test suite with three judge assertions and an execution policy of 3 runs per item, 2 to pass.

The voicemails cover the interesting range: a poisoning (emergency), a limping cat that is still eating (same-day), a rabbit vaccination booking (routine), and one caller who mixes a same-day problem with a nail trim for a second dog, so the urgency must follow the worse of the two.

## See it in Opik

Open the **`whisper-vet-voicemail-triage`** project and the **Traces** tab. After one run of `main.py` you get four `triage-voicemail` traces, one per voicemail. Open one (say the `xylitol-gum` one) and you will see:

- A span tree: `triage-voicemail` at the root, then `synthesize-voicemail` (containing an `audio.speech.create` llm span for `tts-1`, about $0.004 for that clip), `transcribe`, and `triage` (containing a `chat_completion_create` llm span for `gpt-4o-mini` with token counts and a cost around $0.0001).
- On the trace itself, an **attachment**, `xylitol-gum.mp3`, with an inline player. Press play and you hear the exact recording the pipeline processed, right beside the `transcribe` output and the JSON triage. That is how you settle "Whisper's fault or the model's fault" in ten seconds.
- The `transcribe` span is a plain span with no model or cost: `track_openai` does not turn the Whisper call into an llm span, so its text output is the thing to look at there.

Then open the **Test suites** area and the suite **`vet-voicemail-triage-suite`**: 4 items, 3 assertions, execution policy `runs_per_item=3`, `pass_threshold=2`. Each `evaluate.py` run is an experiment; in the last run each item ran three times, so the experiment shows 12 runs, and each assertion shows a pass count out of 12 plus the judge's reason for any failure. Those 12 runs also appear in the project as `evaluation_task` traces.

How the judge behaved on the same four voicemails in two runs:

| Judge model | Items passed | Urgency assertion |
|---|---|---|
| `gpt-4o-mini` | 3 of 4 | 9 of 12 |
| `gpt-4.1-mini` | 4 of 4 | 12 of 12 |

With the `gpt-4o-mini` judge, the `limping-cat` item failed even though the triage said `same-day`, which is correct. Two of the three runs of the judge produced reasons like "The urgency is 'same-day', not 'emergency' as per the transcript", which contradicts itself. One flipped verdict is exactly what the 2-of-3 policy absorbs; two flipped verdicts on one item is more than it can, so the fix was a better judge, not a looser threshold.

## Run it yourself

1. `cd whisper-vet-voicemail-triage`
2. `cp .env.example .env` and fill it in (or rely on a repo-level `.env` one folder up; the scripts load that too). Needs `OPENAI_API_KEY`, and Opik credentials, or `OPIK_URL_OVERRIDE` for a self-hosted Opik.
3. `uv sync`
4. `uv run main.py`: speaks, transcribes and triages the four voicemails (about 45 seconds, a few cents), then prints the callback queue.
5. `uv run evaluate.py`: runs the suite against the transcripts `main.py` just wrote to `output/` (about 10 seconds with the default judge).
6. Open the project in Opik, open any `triage-voicemail` trace, and press play on the attachment.

Run the offline tests with no keys and tracking off:

```
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
```

Everything here is fictional: the callers, the pets, the phone numbers, and the clinic. The voices are OpenAI TTS.

## Poke around

- Change `JUDGE_MODEL` in `evaluate.py` back to `gpt-4o-mini` and run the suite twice. Compare the per-assertion pass counts between experiments.
- Set `pass_threshold` to 3 in both places in `evaluate.py` and see how many items now fail on judge noise alone.
- Weaken the "mixed problems take the most serious urgency" rule in `triage.py` and watch the `two-pets-mixed` item go red in the suite.
- Add a fifth voicemail with a phone number spoken as words ("five five five, oh one...") and compare the number in the transcript with the number in the callback entry.

## Gotchas we hit

**`TypeError: DatasetItem() got multiple values for keyword argument 'id'` when inserting suite items.**
The suite item's `data` dict is unpacked into a `DatasetItem`, which already has an `id` field. A key named `id` in your data collides with it. Use another name: `suite.insert([{"data": {"voicemail": record["id"], "transcript": ...}}])`.

**The suite fails an item whose output is plainly correct, and the judge's reason argues with itself.**
With `model="gpt-4o-mini"` as judge, the `limping-cat` item failed (urgency assertion 9/12 overall) while the output said `same-day`. A runs-per-item policy only absorbs occasional flips. If the judge is wrong most of the time, it cannot save you. Pass a stronger judge: `opik.run_tests(test_suite=suite, task=task, model="gpt-4.1-mini")`, which gave 12/12 here.

**The callback says "Ingrid Larson" but the script says "Larsen".**
Whisper spelled the surname differently in every run we did. The triage is faithful to the transcript, not to the script, so the assertions compare against the transcript too. This is also why the attachment matters: the recording is the only place you can tell which spelling was actually spoken. Do not "fix" it in the prompt; verify names with the caller.

**The `transcribe` span shows no cost or model.**
`track_openai` records the TTS call and the chat call as llm spans, but the Whisper call only appears inside your own `@opik.track(name="transcribe")` span. Put whatever you want to remember (the model name, the audio duration) in that span's metadata.

## How it's put together

- `main.py`: the pipeline (TTS, Whisper, triage), the Opik tracing, and the MP3 attachment; prints the callback queue.
- `triage.py`: the triage prompt, the reply validator, and the callback-queue ordering. No model calls, so it is unit-testable.
- `evaluate.py`: the Opik test suite: three judge assertions, a 3-runs / 2-to-pass execution policy, one experiment per run.
- `data/voicemails.json`: four fictional voicemail scripts with a TTS voice and an expected urgency each.
- `tests/test_triage.py`: offline tests for the validator, queue ordering, data shape, and a traced function called with tracking disabled.
- `.env.example`, `.gitignore`: the keys needed; `output/` (audio, transcripts) and suite reports are git-ignored.

---

*built with Opik · inspired by Opik's examples and documentation*
