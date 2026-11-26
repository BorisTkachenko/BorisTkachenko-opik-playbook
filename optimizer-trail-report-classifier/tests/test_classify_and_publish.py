import types

from trailclass import classify as classify_module
from trailclass.optimize import strip_placeholder
from trailclass.opik_assets import to_mustache
from trailclass.publish import should_publish


class FakeClient:
    """Stands in for the traced OpenAI client; records what the prompt looked like."""

    def __init__(self):
        self.calls = []
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = types.SimpleNamespace(content='{"category": "trail_hazard"}')
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def test_traced_classify_runs_with_tracking_disabled(monkeypatch):
    # classify is wrapped in @opik.track; with OPIK_TRACK_DISABLE=true it is a plain call.
    fake = FakeClient()
    monkeypatch.setattr(classify_module, "_client", lambda: fake)
    assert classify_module.classify("sys", "A tree is down on Fernwood Loop") == '{"category": "trail_hazard"}'
    sent = fake.calls[0]["messages"]
    assert sent[0] == {"role": "system", "content": "sys"}
    assert fake.calls[0]["response_format"]["json_schema"]["strict"] is True
    assert sent[1]["content"] == "A tree is down on Fernwood Loop"


def test_library_template_uses_mustache():
    assert to_mustache("{report}") == "{{report}}"


def test_publish_requires_a_clear_heldout_gain_from_a_different_prompt():
    assert should_publish("old", "new", 0.50, 0.75)
    assert not should_publish("old", "new", 0.50, 0.54)  # within noise
    assert not should_publish("old", "new", 0.60, 0.50)
    assert not should_publish("same", "same ", 0.10, 0.90)  # the "winner" is the baseline text


def test_stray_report_placeholder_is_removed_from_system_text():
    messy = "Respond with the exact category: {report}."
    assert strip_placeholder(messy) == "Respond with the exact category."
    assert strip_placeholder("No placeholder here.") == "No placeholder here."
