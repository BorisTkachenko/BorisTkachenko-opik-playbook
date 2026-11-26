"""The Opik test suite: per-label assertions that carry the expected values."""

from typing import Any

import opik

from .config import LABELS_DIR, MODEL, PROJECT_NAME
from .extract import extract_label
from .render import load_products

# Rules every extraction must satisfy, judged from the output alone.
GLOBAL_ASSERTIONS = [
    "The output contains all ten fields (product_name, serving_size, servings_per_container, "
    "calories, total_fat_g, sodium_mg, total_carbs_g, sugars_g, protein_g, allergens)",
    "Numeric fields are numbers or null, never strings, and allergens is a list",
    "No value is invented: a field that is null is not replaced by a typical-looking number",
]


def _num(v: float) -> str:
    return f"{v:g}"


def assertions_for(product: dict[str, Any]) -> list[str]:
    """Plain-language assertions holding the expected values for one product.

    The expected values live only in the assertions: the judge compares the output to
    them, so the test input (just an image file name) never leaks the answer.
    """
    sodium = (
        "sodium_mg is null because the label does not print a sodium line"
        if product["sodium_mg"] is None
        else f"sodium_mg is {_num(product['sodium_mg'])}"
    )
    allergens = ", ".join(product["allergens"]) or "none (an empty list)"
    return [
        f"product_name is {product['brand']}, serving_size is {product['serving_size']}, "
        f"and servings_per_container is {_num(product['servings_per_container'])}",
        f"calories is {_num(product['calories'])}, total_fat_g is {_num(product['total_fat_g'])}, "
        f"and {sodium}",
        f"total_carbs_g is {_num(product['total_carbs_g'])}, sugars_g is {_num(product['sugars_g'])}, "
        f"and protein_g is {_num(product['protein_g'])}",
        f"allergens contain exactly these items, in any order and with no extras: {allergens}",
    ]


def build_items() -> list[dict[str, Any]]:
    return [
        {
            "data": {"image": str(LABELS_DIR / f"{p['id']}.png"), "note": p["style"]["note"]},
            "assertions": assertions_for(p),
        }
        for p in load_products()
    ]


def run_suite() -> Any:
    client = opik.Opik(project_name=PROJECT_NAME)
    # A test suite = items plus judge assertions. The suite lives in Opik, one per project.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME, project_name=PROJECT_NAME, global_assertions=GLOBAL_ASSERTIONS
    )
    # get_or_create_test_suite keeps an existing suite as it was: edited global assertions are
    # ignored and re-inserting changed items would pile up beside the old ones. Sync both
    # explicitly so the suite in Opik always matches this file.
    suite.update_test_settings(global_assertions=GLOBAL_ASSERTIONS)
    suite.clear()
    suite.insert(build_items())

    def task(item: dict[str, Any]) -> dict[str, Any]:
        # Calling the traced function means every suite item also produces a trace
        # with the label attached, linked to the experiment row.
        return {"input": item, "output": extract_label(item["image"])}

    # run_tests extracts each label, has an LLM judge grade every assertion and
    # records an experiment you can open in the Test suites tab.
    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=f"nutrition-labels-{MODEL}",
        worker_threads=3,
        generate_report=False,
    )
    client.flush()
    return result
