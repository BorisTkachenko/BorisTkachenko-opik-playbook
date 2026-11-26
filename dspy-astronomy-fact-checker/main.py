"""Run the claim checker uncompiled and compiled, and print both scores."""

import pathlib

import dotenv
import dspy

import checker

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
    dspy.configure(lm=checker.make_lm())
    program = checker.build_program()
    print("uncompiled:", score(program))
    compiled = checker.compile_program(program)
    print("compiled:  ", score(compiled))


if __name__ == "__main__":
    main()
