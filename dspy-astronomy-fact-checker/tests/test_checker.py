"""Offline tests: no provider key, no Opik, tracking disabled."""

import dspy
import pytest

import checker
from metrics import DecisionCorrect, EvidenceInHouseForm, FullyCorrect


@pytest.mark.parametrize("raw,expected", [
    ("SUPPORTED", "SUPPORTED"),
    ("  supported. ", "SUPPORTED"),
    ("Not enough info", "NOT_ENOUGH_INFO"),
    ("not_enough_info", "NOT_ENOUGH_INFO"),
    ("The claim is true.", "THE_CLAIM_IS_TRUE"),
    ("True", "TRUE"),
])
def test_normalise_verdict_ignores_typography_but_not_meaning(raw, expected):
    assert checker.normalise_verdict(raw) == expected


def test_prose_evidence_is_not_a_house_style_id():
    row = {"evidence": "F-06"}
    assert checker.evidence_correct(row, "[f-06]")
    assert checker.evidence_correct(row, " F-06. ")
    assert not checker.evidence_correct(row, "[F-06] Calix is a gas giant")
    assert checker.evidence_correct({"evidence": "NONE"}, "none")


def test_data_is_consistent():
    ids = {line[1:5] for line in checker.FACT_SHEET.splitlines() if line.startswith("[F-")}
    for row in checker.testset() + [dict(claim=e.claim, label=e.verdict, evidence=e.evidence) for e in checker.trainset()]:
        assert row["label"] in checker.LABELS
        assert row["evidence"] in ids | {"NONE"}
        assert (row["label"] == "NOT_ENOUGH_INFO") == (row["evidence"] == "NONE")
    assert {e.verdict for e in checker.trainset()} == set(checker.LABELS)


def test_house_metric_needs_decision_and_evidence():
    ex = checker.to_example({"claim": "c", "label": "REFUTED", "evidence": "F-06"})
    assert checker.house_metric(ex, dspy.Prediction(verdict="refuted", evidence="F-06"))
    assert not checker.house_metric(ex, dspy.Prediction(verdict="The claim is false.", evidence="F-06"))
    assert not checker.house_metric(ex, dspy.Prediction(verdict="REFUTED", evidence="see F-06"))


def test_metrics_score_one_or_zero():
    assert DecisionCorrect().score("Supported", "SUPPORTED").value == 1.0
    assert EvidenceInHouseForm().score("F-01", "F-01").value == 1.0
    assert FullyCorrect().score("True", "F-01", "SUPPORTED", "F-01").value == 0.0


class StubProgram(dspy.Module):
    """Stands in for the ChainOfThought program: no LM, fixed answer."""

    def forward(self, fact_sheet, claim):
        return dspy.Prediction(reasoning="r", verdict="SUPPORTED", evidence="F-01")


def test_task_runs_with_tracking_disabled():
    # main.py imports the Opik integration at module level; with
    # OPIK_TRACK_DISABLE=true the task that evaluate() calls runs untouched.
    import main

    out = main.make_task(StubProgram())({"claim": "Veyra is binary."})
    assert out == {"verdict": "SUPPORTED", "evidence": "F-01", "reasoning": "r"}
