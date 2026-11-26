"""Offline data helpers for the wedding-planner crew (no LLM, no Opik)."""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def load_venues() -> list[dict]:
    return json.loads((DATA / "venues.json").read_text())


def load_vendors() -> dict[str, list[dict]]:
    return json.loads((DATA / "vendors.json").read_text())


def load_couple() -> str:
    return (DATA / "couple.md").read_text()


def fitting_venues(venues: list[dict], guests: int) -> list[dict]:
    """Venues whose capacity holds the guest list, cheapest first."""
    return sorted((v for v in venues if v["capacity"] >= guests), key=lambda v: v["rental_usd"])


def vendor_total(vendors: dict[str, list[dict]], picks: dict[str, str], guests: int) -> int:
    """Sum the chosen vendors' prices; catering is per guest, the rest is flat."""
    total = 0
    for category, name in picks.items():
        item = next(v for v in vendors[category] if v["name"] == name)
        total += item["per_guest_usd"] * guests if "per_guest_usd" in item else item["flat_usd"]
    return total


def format_venues(venues: list[dict]) -> str:
    return "\n".join(
        f"- {v['name']}: {v['setting']}, up to {v['capacity']} guests, ${v['rental_usd']:,} rental. {v['notes']}"
        for v in venues
    )


def format_vendors(vendors: dict[str, list[dict]]) -> str:
    lines = []
    for category, items in vendors.items():
        lines.append(f"{category.title()}:")
        for v in items:
            price = f"${v['per_guest_usd']}/guest" if "per_guest_usd" in v else f"${v['flat_usd']:,} flat"
            lines.append(f"- {v['name']}: {price}, {v['style']}")
    return "\n".join(lines)
