"""Run the claim checker uncompiled and compiled, and print both scores."""

import os
import pathlib

PROJECT_NAME = "dspy-astronomy-fact-checker"
# Set before the first traced call so nothing lands in "Default Project".
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import dotenv
import dspy
import opik
from opik.integrations.dspy.callback import OpikCallback

import checker

# Repo-root .env: provider key plus (optionally) OPIK_URL_OVERRIDE / OPIK_WORKSPACE.
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")


def score(program: dspy.Module) -> dict:
    rows = checker.testset()
    decision = evidence = both = 0
    for row in rows:
        pred = program(fact_sheet=checker.FACT_SHEET, claim=row["claim"])
        d = checker.decision_correct(row, pred.verdict)
        e = checker.evidence_correct(row, pred.evidence)
        decision, evidence, both = decision + d, evidence + e, both + (d and e)
    return {"decision": decision, "evidence": evidence, "both": both, "n": len(rows)}


def main() -> None:
    # OpikCallback turns every DSPy module and LM call into a trace: the
    # ChainOfThought/Predict spans, and a nested llm span with usage and
    # cost. log_graph=True also stores the module graph on the trace.
    dspy.configure(
        lm=checker.make_lm(),
        callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)],
    )
    program = checker.build_program()
    print("uncompiled:", score(program))
    compiled = checker.compile_program(program)
    print("compiled:  ", score(compiled))
    # Traces ship from a background thread; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
