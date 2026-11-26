import json

from flashcards import CARD_FIELDS, build_messages, parse_card

GOOD = {"front": "saudade", "back": "longing", "example": "Tenho saudade.", "mnemonic": "Sad-ade."}


def test_build_messages_includes_word_and_context():
    msgs = build_messages({"word": "cafuné", "context": "Ela fez cafuné."})
    assert msgs[0]["role"] == "system" and msgs[1]["role"] == "user"
    assert "cafuné" in msgs[1]["content"] and "Ela fez cafuné." in msgs[1]["content"]


def test_parse_card_accepts_fixed_shape_and_strips_fences():
    assert parse_card(json.dumps(GOOD)) == GOOD
    assert parse_card("```json\n" + json.dumps(GOOD) + "\n```") == GOOD


def test_parse_card_rejects_bad_shapes():
    assert parse_card("no json here") is None
    assert parse_card("{not json}") is None
    for missing in CARD_FIELDS:
        assert parse_card(json.dumps({k: v for k, v in GOOD.items() if k != missing})) is None
    assert parse_card(json.dumps({**GOOD, "back": "  "})) is None
