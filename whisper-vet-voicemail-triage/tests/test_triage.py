"""Offline tests: no provider keys, no Opik. Run with
    env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
"""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")  # client construction only; never called
os.environ["OPIK_TRACK_DISABLE"] = "true"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main
from triage import TriageError, callback_queue, parse_triage

GOOD = {
    "urgency": "emergency",
    "urgency_reason": "ate xylitol gum",
    "callbacks": [{"owner": "Marta", "pet": "Biscuit", "number": "555-0142", "reason": "poisoning"}],
}


def test_parse_triage_accepts_valid_reply():
    assert parse_triage(json.dumps(GOOD))["urgency"] == "emergency"


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        json.dumps({**GOOD, "urgency": "urgent"}),
        json.dumps({**GOOD, "callbacks": "none"}),
        json.dumps({**GOOD, "callbacks": [{"owner": "Marta"}]}),
    ],
)
def test_parse_triage_rejects_bad_replies(bad):
    with pytest.raises(TriageError):
        parse_triage(bad)


def test_callback_queue_orders_by_urgency():
    def result(level, owner):
        return {"urgency": level, "callbacks": [{"owner": owner, "pet": "p", "number": "n", "reason": "r"}]}

    queue = callback_queue([result("routine", "a"), result("emergency", "b"), result("same-day", "c")])
    assert [row["owner"] for row in queue] == ["b", "c", "a"]


def test_voicemail_data_is_well_formed():
    voicemails = main.load_voicemails()
    assert {v["expected_urgency"] for v in voicemails} == {"emergency", "same-day", "routine"}
    assert all(v["script"] and v["voice"] for v in voicemails)


def test_traced_triage_runs_with_tracking_disabled(monkeypatch):
    """@opik.track and track_openai must not get in the way of a stubbed model call."""
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(GOOD)))])
    monkeypatch.setattr(
        main.openai_client.chat.completions, "create", lambda **kwargs: reply
    )
    assert main.triage_transcript("my dog ate gum")["callbacks"][0]["pet"] == "Biscuit"
