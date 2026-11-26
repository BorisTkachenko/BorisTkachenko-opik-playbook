"""Flashcard prompt, JSON parsing and validation (no network, no tracing)."""

import json
import re

CARD_FIELDS = ("front", "back", "example", "mnemonic")

SYSTEM_PROMPT = (
    "You are a Portuguese tutor for English-speaking beginners. "
    "Reply with ONE JSON object and nothing else, with exactly these string keys: "
    '"front" (the Portuguese word), "back" (its English meaning, under 12 words), '
    '"example" (a new Portuguese sentence using the word), '
    '"mnemonic" (a one-sentence memory trick). No markdown fences.'
)


def build_messages(entry: dict) -> list[dict]:
    """Chat messages asking for one flashcard for a vocabulary entry."""
    user = f"Word: {entry['word']}\nSeen in this sentence: {entry['context']}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def parse_card(text: str) -> dict | None:
    """Parse a model reply into a card dict, or None if it is not the fixed shape."""
    match = re.search(r"\{.*\}", text, re.DOTALL)  # tolerate fences / chatter
    if not match:
        return None
    try:
        card = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(card, dict):
        return None
    if not all(isinstance(card.get(k), str) and card[k].strip() for k in CARD_FIELDS):
        return None
    return {k: card[k].strip() for k in CARD_FIELDS}
