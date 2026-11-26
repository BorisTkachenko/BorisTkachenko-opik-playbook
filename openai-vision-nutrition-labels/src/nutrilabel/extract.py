"""Send a label image to OpenAI vision and get typed nutrition facts back."""

import base64
from pathlib import Path
from typing import Any

import opik
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai
from openai import OpenAI

from .config import MODEL, PROJECT_NAME, load_env
from .schema import JSON_SCHEMA, NutritionFacts, parse_facts

SYSTEM_PROMPT = """\
You read photos of nutrition-facts labels and extract fields. Read only what is
printed on the image. If a line is not on the label or you cannot read it, return
null for that field: never guess, never fill in a typical value.

- product_name: the product name printed at the top.
- serving_size: the serving size text exactly as printed.
- servings_per_container: the number of servings per container.
- calories, total_fat_g, sodium_mg, total_carbs_g, sugars_g, protein_g: numbers
  per serving, without units.
- allergens: the items listed after "Contains:", lower-case; an empty list if
  the label has no allergen line."""

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Build the traced client lazily so importing this module needs no API key."""
    global _client
    if _client is None:
        load_env()
        # track_openai wraps the client: every chat completion becomes an llm span
        # with token usage and estimated cost, nested under the calling trace.
        _client = track_openai(OpenAI(), project_name=PROJECT_NAME)
    return _client


def image_message(path: Path) -> dict[str, Any]:
    b64 = base64.b64encode(path.read_bytes()).decode()
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract the nutrition facts from this label."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}},
        ],
    }


# @opik.track opens the trace for one label (a general span as the root); the OpenAI
# call below nests inside it as an llm span.
@opik.track(name="extract_label", project_name=PROJECT_NAME)
def extract_label(image_path: str) -> dict[str, Any]:
    path = Path(image_path)
    # Attachment on the trace: the Attachments tab shows the exact PNG the model saw,
    # next to the fields it returned. Without this you only get a base64 blob in the span.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(path), content_type="image/png", file_name=path.name)],
        tags=["nutrition-label"],
    )
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, image_message(path)],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "nutrition_facts", "strict": True, "schema": JSON_SCHEMA},
        },
    )
    facts: NutritionFacts = parse_facts(response.choices[0].message.content)
    return facts.to_dict()
