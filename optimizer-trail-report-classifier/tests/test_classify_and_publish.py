import types

from trailclass import classify as classify_module
from trailclass.opik_assets import to_mustache
from trailclass.publish import should_publish


class FakeClient:
    """Stands in for the traced OpenAI client; records what the prompt looked like."""

    def __init__(self):
        self.calls = []
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = types.SimpleNamespace(content="trail_hazard")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def test_traced_classify_runs_with_tracking_disabled(monkeypatch):
    # classify is wrapped in @opik.track; with OPIK_TRACK_DISABLE=true it is a plain call.
    fake = FakeClient()
    monkeypatch.setattr(classify_module, "_client", lambda: fake)
    assert classify_module.classify("sys", "A tree is down on Fernwood Loop") == "trail_hazard"
    sent = fake.calls[0]["messages"]
    assert sent[0] == {"role": "system", "content": "sys"}
    assert sent[1]["content"] == "A tree is down on Fernwood Loop"


def test_library_template_uses_mustache():
    assert to_mustache("{report}") == "{{report}}"


def test_publish_requires_a_heldout_gain():
    assert should_publish(0.33, 0.61)
    assert not should_publish(0.61, 0.61)
    assert not should_publish(0.61, 0.5)
