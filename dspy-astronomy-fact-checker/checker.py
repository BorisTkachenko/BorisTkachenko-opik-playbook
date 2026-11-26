"""The claim checker: a DSPy program, its data and its scoring rules.

Nothing in this module talks to Opik, so it is also what the offline tests
exercise. Given a claim about the fictional Veyra star system, the program
returns a verdict and the id of the fact-sheet line it relied on.
"""

import json
import os
import pathlib
import re

import dspy

DATA = pathlib.Path(__file__).parent / "data"
MODEL = "openai/gpt-4o-mini"

FACT_SHEET = (DATA / "factsheet.txt").read_text()
_CLAIMS = json.loads((DATA / "claims.json").read_text())

LABELS = ("SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO")


class CheckClaim(dspy.Signature):
    """Check a claim against the fact sheet."""

    fact_sheet: str = dspy.InputField()
    claim: str = dspy.InputField()
    verdict: str = dspy.OutputField(desc="the decision on the claim")
    evidence: str = dspy.OutputField(desc="the fact-sheet line the decision rests on")


# Deliberately silent about the label set and the evidence format: the
# docstring and field descriptions say only "decide" and "point at the line".
# The house conventions exist solely in the worked examples (the trainset).
def build_program() -> dspy.Module:
    return dspy.ChainOfThought(CheckClaim)


def make_lm() -> dspy.LM:
    # Unset proxy overrides so the example always reaches the public API.
    for var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
        os.environ.pop(var, None)
    return dspy.LM(MODEL, cache=False, temperature=0.0)


def to_example(row: dict) -> dspy.Example:
    return dspy.Example(
        fact_sheet=FACT_SHEET,
        claim=row["claim"],
        verdict=row["label"],
        evidence=row["evidence"],
    ).with_inputs("fact_sheet", "claim")


def trainset() -> list[dspy.Example]:
    return [to_example(r) for r in _CLAIMS["train"]]


def testset() -> list[dict]:
    return list(_CLAIMS["test"])


# --- Scoring: measure the decision, not the typography ----------------------

def normalise_verdict(text: str) -> str:
    """'Not enough info.', 'not_enough_info' and 'NOT ENOUGH INFO' are one label."""
    return re.sub(r"[^A-Z]+", "_", (text or "").upper()).strip("_")


def normalise_evidence(text: str) -> str:
    """Reduce an evidence field to a bare id: '[f-06]', ' F-06. ' -> 'F-06'.

    Anything that is not exactly one fact id (or NONE) comes back unchanged
    in upper case, so a prose sentence can never be mistaken for an id.
    """
    cleaned = (text or "").strip().strip("[]().,;:").strip().upper()
    return cleaned


def decision_correct(row: dict, verdict: str) -> bool:
    return normalise_verdict(verdict) == row["label"]


def evidence_correct(row: dict, evidence: str) -> bool:
    return normalise_evidence(evidence) == row["evidence"]


def house_metric(example: dspy.Example, prediction, trace=None) -> bool:
    """Compile-time metric: right decision AND the evidence line in house form."""
    row = {"label": example.verdict, "evidence": example.evidence}
    return decision_correct(row, prediction.verdict) and evidence_correct(
        row, prediction.evidence
    )


def compile_program(program: dspy.Module) -> dspy.Module:
    """Few-shot optimise the program on the trainset with BootstrapFewShot."""
    optimizer = dspy.BootstrapFewShot(
        metric=house_metric,
        max_bootstrapped_demos=4,
        # 8 = the whole trainset: labeled demos top the prompt up to every
        # row, so the demo set never depends on sampling luck.
        max_labeled_demos=8,
        max_rounds=1,
    )
    return optimizer.compile(program, trainset=trainset())
