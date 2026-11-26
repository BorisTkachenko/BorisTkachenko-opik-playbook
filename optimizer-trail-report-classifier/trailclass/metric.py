"""Exact-match scoring, shared by the baseline, the optimizer and the holdout check."""

import re

from opik.evaluation.metrics import base_metric, score_result

from .config import LABELS


def normalize(answer: str) -> str:
    """Lowercase, drop quotes/punctuation, and read spaces or hyphens as underscores.

    "Trail hazard." counts as trail_hazard, but a sentence that merely mentions
    the category does not: the output format is part of what is being scored.
    """
    cleaned = answer.strip().lower().strip(".!\"'`* ")
    return re.sub(r"[\s-]+", "_", cleaned)


def is_correct(answer: str, label: str) -> bool:
    return normalize(answer) == label


def trail_report_accuracy(dataset_item: dict, llm_output: str) -> float:
    """Metric signature the optimizer expects: (dataset_item, llm_output) -> score."""
    return 1.0 if is_correct(llm_output, dataset_item["label"]) else 0.0


def is_known_label(answer: str) -> bool:
    return normalize(answer) in LABELS


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
