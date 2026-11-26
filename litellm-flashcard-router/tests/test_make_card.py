import json
from types import SimpleNamespace

import main

REPLY = json.dumps({"front": "saudade", "back": "longing", "example": "Tenho saudade.", "mnemonic": "Sad."})


def fake_completion(**kwargs):
    # Stands in for litellm.completion: no network, no provider key.
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=REPLY))],
        usage=SimpleNamespace(total_tokens=42),
        _hidden_params={"response_cost": 0.0001},
    )


def test_traced_make_card_runs_with_tracking_disabled(monkeypatch):
    # With OPIK_TRACK_DISABLE=true, @opik.track is a pass-through, so the traced function is unit-testable.
    monkeypatch.setattr(main.litellm, "completion", fake_completion)
    out = main.make_card("openai/gpt-4o-mini", {"word": "saudade", "context": "..."})
    assert out["card"]["back"] == "longing" and out["tokens"] == 42 and out["cost"] == 0.0001
