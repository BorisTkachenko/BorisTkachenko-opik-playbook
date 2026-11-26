"""Pure triage logic: the prompt, the output schema, and its validation.

Nothing here talks to a model, so it is easy to unit test.
"""

import json

URGENCY_LEVELS = ("emergency", "same-day", "routine")

TRIAGE_SYSTEM_PROMPT = """\
You are the front-desk triage assistant for a veterinary clinic. You read the
transcript of one voicemail and reply with JSON only, in exactly this shape:

{
  "urgency": "emergency" | "same-day" | "routine",
  "urgency_reason": "one sentence citing what the caller said",
  "callbacks": [
    {"owner": "caller's name", "pet": "pet's name", "number": "phone number", "reason": "why the clinic should call back"}
  ]
}

Urgency levels:
- emergency: possible poisoning, trouble breathing, collapse, seizures, heavy
  bleeding, or anything where waiting an hour could cost the animal's life.
- same-day: the animal is unwell or in pain but stable and still eating or
  drinking; it should be seen today.
- routine: bookings, vaccinations, grooming, refills, and questions.

Rules:
- A voicemail that mentions several problems takes the urgency of the most
  serious one.
- Write one callback entry per pet the caller mentioned, with the same owner
  and number. Copy names and the phone number exactly as transcribed.
- If a detail is not in the transcript, use null. Never invent one.
"""


class TriageError(ValueError):
    """The model's reply did not match the triage schema."""


def parse_triage(raw: str) -> dict:
    """Parse and validate the model's JSON reply."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TriageError(f"reply is not JSON: {exc}") from exc
    if data.get("urgency") not in URGENCY_LEVELS:
        raise TriageError(f"urgency must be one of {URGENCY_LEVELS}, got {data.get('urgency')!r}")
    callbacks = data.get("callbacks")
    if not isinstance(callbacks, list):
        raise TriageError("callbacks must be a list")
    for entry in callbacks:
        missing = {"owner", "pet", "number", "reason"} - set(entry)
        if missing:
            raise TriageError(f"callback is missing {sorted(missing)}")
    return data


def callback_queue(results: list[dict]) -> list[dict]:
    """Flatten per-voicemail triage into one callback list, most urgent first."""
    rank = {level: i for i, level in enumerate(URGENCY_LEVELS)}
    rows = [
        {"urgency": r["urgency"], **entry}
        for r in results
        for entry in r["callbacks"]
    ]
    return sorted(rows, key=lambda row: rank[row["urgency"]])
