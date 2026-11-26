"""The typed record we extract from a label, plus parsing of the model's JSON reply."""

import json
from dataclasses import asdict, dataclass, field
from typing import Any

# Numeric fields share one rule: a number, or null when the label does not print it.
NUMERIC_FIELDS = [
    "servings_per_container",
    "calories",
    "total_fat_g",
    "sodium_mg",
    "total_carbs_g",
    "sugars_g",
    "protein_g",
]


@dataclass
class NutritionFacts:
    product_name: str | None = None
    serving_size: str | None = None
    servings_per_container: float | None = None
    calories: float | None = None
    total_fat_g: float | None = None
    sodium_mg: float | None = None
    total_carbs_g: float | None = None
    sugars_g: float | None = None
    protein_g: float | None = None
    allergens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nullable(kind: str, description: str) -> dict[str, Any]:
    return {"type": [kind, "null"], "description": description}


# Strict JSON schema for OpenAI structured outputs: every field required, but
# nullable so a missing line can be reported as null instead of invented.
JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "product_name": _nullable("string", "product name as printed"),
        "serving_size": _nullable("string", "serving size text, e.g. '1 cup (240ml)'"),
        "servings_per_container": _nullable("number", "servings per container"),
        "calories": _nullable("number", "calories per serving"),
        "total_fat_g": _nullable("number", "total fat in grams"),
        "sodium_mg": _nullable("number", "sodium in milligrams"),
        "total_carbs_g": _nullable("number", "total carbohydrate in grams"),
        "sugars_g": _nullable("number", "total sugars in grams"),
        "protein_g": _nullable("number", "protein in grams"),
        "allergens": {"type": "array", "items": {"type": "string"}, "description": "allergens listed after 'Contains'"},
    },
    "required": [
        "product_name", "serving_size", "servings_per_container", "calories", "total_fat_g",
        "sodium_mg", "total_carbs_g", "sugars_g", "protein_g", "allergens",
    ],
    "additionalProperties": False,
}


def parse_facts(raw: str) -> NutritionFacts:
    """Turn the model's JSON text into a NutritionFacts, tolerating bad types."""
    data = json.loads(raw)
    facts = NutritionFacts(
        product_name=data.get("product_name"),
        serving_size=data.get("serving_size"),
    )
    for name in NUMERIC_FIELDS:
        value = data.get(name)
        # Booleans are ints in Python; a label never prints one, so treat them as junk.
        setattr(facts, name, float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None)
    allergens = data.get("allergens") or []
    facts.allergens = sorted({str(a).strip().lower() for a in allergens if str(a).strip()})
    return facts
