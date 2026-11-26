"""Read the project's llm spans back from Opik and print the same per-model table.

Run after main.py:  uv run check_opik.py
Exits non-zero if any llm span has no estimated cost (an unpriced model).
"""

import sys

import opik

from report import format_table

PROJECT = "litellm-flashcard-router"


def rows_from_spans(spans) -> tuple[list[dict], int]:
    """Group llm spans by model; returns (rows, number of spans with null cost)."""
    by_model: dict[str, list] = {}
    for s in spans:
        if s.type == "llm":
            by_model.setdefault(s.model or "unknown", []).append(s)
    rows, null_cost = [], 0
    for model, group in sorted(by_model.items()):
        null_cost += sum(s.total_estimated_cost is None for s in group)
        lat = [(s.end_time - s.start_time).total_seconds() for s in group]
        rows.append({
            "model": model, "ok": len(group), "calls": len(group),
            "tokens": sum((s.usage or {}).get("total_tokens", 0) for s in group),
            "cost": sum(s.total_estimated_cost or 0.0 for s in group),
            "mean_latency": sum(lat) / len(lat),
        })
    return rows, null_cost


def main() -> int:
    # search_spans reads the llm spans the OpikLogger callback wrote, with cost computed by Opik.
    spans = opik.Opik().search_spans(project_name=PROJECT, max_results=1000)
    rows, null_cost = rows_from_spans(spans)
    print(format_table(rows))
    print(f"\nllm spans with null cost: {null_cost}")
    return 1 if null_cost or not rows else 0


if __name__ == "__main__":
    sys.exit(main())
