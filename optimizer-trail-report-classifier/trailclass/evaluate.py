"""Score a system prompt over a list of labelled rows."""

from .classify import classify
from .metric import is_correct


def accuracy(system_prompt: str, rows: list[dict]) -> tuple[float, list[dict]]:
    """Return (accuracy, per-row results) for a prompt over the rows."""
    results = []
    for row in rows:
        answer = classify(system_prompt, row["report"])
        results.append({"label": row["label"], "answer": answer, "ok": is_correct(answer, row["label"])})
    return sum(r["ok"] for r in results) / len(results), results
