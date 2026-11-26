"""Test suite for the triage step: is the urgency call right, is the callback list faithful?

A wrong urgency is the expensive failure here: a poisoned dog filed as
"routine" waits in the queue. This suite pushes each transcript produced by
main.py back through the triage step and has an LLM judge check three
assertions against the transcript. Run `uv run main.py` first; it writes
the transcripts to output/.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")
os.environ["OPIK_PROJECT_NAME"] = "whisper-vet-voicemail-triage"
os.environ.pop("OPENAI_BASE_URL", None)

import opik

from main import triage_transcript

SUITE_NAME = "vet-voicemail-triage-suite"
PROJECT_NAME = "whisper-vet-voicemail-triage"

ASSERTIONS = [
    "The urgency is 'emergency' only if the transcript describes a possible "
    "poisoning, breathing trouble, collapse, seizure or heavy bleeding; it is "
    "'same-day' if the animal is unwell or in pain but stable; it is 'routine' "
    "for bookings and other non-urgent requests. If the voicemail mixes "
    "problems, the urgency matches the most serious one.",
    "The callbacks list has exactly one entry per pet the caller mentions, and "
    "each entry's owner and phone number match what the transcript says.",
    "No callback reason or urgency reason states a fact (symptom, time, "
    "medication) that is not in the transcript.",
]

# Judge model for the assertions, passed to run_tests(model=...). gpt-4o-mini
# contradicted itself on correct output (9/12 on the urgency assertion), so a
# stronger judge is used; the execution policy below covers the remaining noise.
JUDGE_MODEL = "gpt-4.1-mini"


def task(item: dict) -> dict:
    """Triage one transcript. The judge sees this input and output."""
    result = triage_transcript(item["transcript"])
    return {"input": {"transcript": item["transcript"]}, "output": result}


if __name__ == "__main__":
    records = [json.loads(p.read_text()) for p in sorted(OUTPUT_DIR.glob("*.json"))]
    if not records:
        raise SystemExit("No transcripts in output/ - run `uv run main.py` first.")

    client = opik.Opik()
    # The suite lives in Opik; each run_tests call below becomes an experiment on it.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=ASSERTIONS,
        # An LLM judge reading an LLM's output is noisy, so a single verdict can
        # flip between runs. Each item runs 3 times and must pass 2: the
        # experiment shows the flake rate instead of failing on one unlucky call.
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    # get_or_create_test_suite ignores assertion/policy changes on an existing
    # suite, so push them explicitly (a no-op when nothing changed).
    suite.update_test_settings(
        global_assertions=ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )

    existing = {item["data"]["voicemail"] for item in suite.get_items()}
    for record in records:
        if record["id"] not in existing:
            suite.insert([{"data": {"voicemail": record["id"], "transcript": record["transcript"]}}])

    result = opik.run_tests(test_suite=suite, task=task, model=JUDGE_MODEL)
    print(f"\nPass rate: {result.pass_rate:.0%}")
    opik.flush_tracker()
