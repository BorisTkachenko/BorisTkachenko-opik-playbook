"""Opik scoring metrics: thin wrappers over the rules in checker.py.

Each one becomes a named column in the experiment table (0 or 1 per claim),
so the two runs can be compared score by score.
"""

from opik.evaluation.metrics import BaseMetric, score_result

import checker


class DecisionCorrect(BaseMetric):
    """1 if the normalised verdict equals the gold label."""

    def __init__(self, name: str = "decision_correct"):
        super().__init__(name=name)

    def score(self, verdict: str, gold_label: str, **ignored) -> score_result.ScoreResult:
        ok = checker.decision_correct({"label": gold_label}, verdict)
        return score_result.ScoreResult(
            name=self.name, value=float(ok),
            reason=f"verdict {verdict!r} -> {checker.normalise_verdict(verdict)!r}, gold {gold_label}",
        )


class EvidenceInHouseForm(BaseMetric):
    """1 if the evidence field is exactly the gold fact id (or NONE)."""

    def __init__(self, name: str = "evidence_correct"):
        super().__init__(name=name)

    def score(self, evidence: str, gold_evidence: str, **ignored) -> score_result.ScoreResult:
        ok = checker.evidence_correct({"evidence": gold_evidence}, evidence)
        return score_result.ScoreResult(
            name=self.name, value=float(ok),
            reason=f"evidence {evidence[:60]!r}, gold {gold_evidence}",
        )


class FullyCorrect(BaseMetric):
    """1 only when both the decision and the evidence line are right."""

    def __init__(self, name: str = "fully_correct"):
        super().__init__(name=name)

    def score(self, verdict: str, evidence: str, gold_label: str, gold_evidence: str, **ignored) -> score_result.ScoreResult:
        ok = checker.decision_correct({"label": gold_label}, verdict) and checker.evidence_correct(
            {"evidence": gold_evidence}, evidence
        )
        return score_result.ScoreResult(name=self.name, value=float(ok))
