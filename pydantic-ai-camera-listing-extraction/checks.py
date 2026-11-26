"""Plain-Python scoring: no model, no Opik. Used by the run summary and the offline tests."""

from typing import Any

FIELDS = ["brand", "model", "mount", "condition", "price_usd", "shutter_count", "accessories", "location"]


def _empty(v: Any) -> bool:
    return v is None or v == [] or v == ""


def invented_fields(listing: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Fields the post leaves empty but the agent filled in: the invented values."""
    return [f for f in FIELDS if _empty(expected.get(f)) and not _empty(listing.get(f))]


def missed_fields(listing: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Fields the post states but the agent left empty."""
    return [f for f in FIELDS if not _empty(expected.get(f)) and _empty(listing.get(f))]
