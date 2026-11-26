"""Exact-match scoring, shared by the baseline, the optimizer and the holdout check."""

import json
import re

from opik.evaluation.metrics import base_metric, score_result

from .config import LABELS


def normalize(answer: str) -> str:
    """Lowercase, drop quotes/punctuation, and read spaces or hyphens as underscores."""
    cleaned = answer.strip().lower().strip(".!\"'`* ")
    return re.sub(r"[\s-]+", "_", cleaned)


def extract_label(answer: str) -> str:
    """Read the category out of a reply, whatever shape it came in.

    Normally the reply is the schema's JSON ({"category": "..."}). If a model or
    a prompt produces anything else, fall back to a normalized bare label, then to
    a short sentence that mentions exactly one label. Anything else is "".
    """
    try:
        parsed = json.loads(answer)
        if isinstance(parsed, dict):
            answer = str(parsed.get("category", ""))
    except ValueError:
        pass
    label = normalize(answer)
    if label in LABELS:
        return label
    spaced = answer.lower().replace("_", " ")
    found = [name for name in LABELS if name.replace("_", " ") in spaced]
    return found[0] if len(found) == 1 and len(answer) < 80 else ""


def is_correct(answer: str, label: str) -> bool:
    return extract_label(answer) == label


def trail_report_accuracy(dataset_item: dict, llm_output: str) -> score_result.ScoreResult:
    """Metric signature the optimizer expects: (dataset_item, llm_output) -> score.

    The reason names the predicted and the expected category: the reflective
    optimizer reads it to work out which kinds of report the prompt gets wrong.
    """
    predicted = extract_label(llm_output) or "unreadable"
    ok = predicted == dataset_item["label"]
    return score_result.ScoreResult(
        name="trail_report_accuracy",
        value=1.0 if ok else 0.0,
        reason=f"report: {dataset_item['report']!r} | predicted {predicted}, expected {dataset_item['label']}",
    )


class CategoryMatch(base_metric.BaseMetric):
    """The same exact-match rule as an Opik scoring metric, for opik.evaluate().

    It shows up as the `category_match` column on each experiment, so the
    baseline and the winner can be compared row by row in the compare view.
    """

    def __init__(self) -> None:
        super().__init__(name="category_match")

    def score(self, output: str, label: str, **_: object) -> score_result.ScoreResult:
        ok = is_correct(output, label)
        return score_result.ScoreResult(
            name=self.name, value=1.0 if ok else 0.0, reason=f"answered {output!r}, expected {label}"
        )
