"""Exact-match scoring, shared by the baseline, the optimizer and the holdout check."""

import re

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
