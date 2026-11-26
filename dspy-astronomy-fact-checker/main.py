"""Compare the uncompiled and the compiled claim checker in Opik.

The same dataset and the same three metrics are evaluated twice, once per
program, as two experiments that Opik can put side by side.
"""

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
from metrics import DecisionCorrect, EvidenceInHouseForm, FullyCorrect

# Repo-root .env: provider key plus (optionally) OPIK_URL_OVERRIDE / OPIK_WORKSPACE.
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

DATASET_NAME = "veyra-claims"


def build_dataset(client: opik.Opik) -> opik.Dataset:
    # Datasets are project-scoped: pass project_name or a later get_dataset
    # by name can 404. This creates the "veyra-claims" dataset in our project.
    dataset = client.get_or_create_dataset(
        name=DATASET_NAME,
        description="Held-out claims about the fictional Veyra system, with gold verdicts.",
    )
    # clear() + insert() makes re-runs idempotent: exactly twelve items, never
    # a pile of duplicates from earlier runs.
    dataset.clear()
    dataset.insert([
        {"claim": r["claim"], "gold_label": r["label"], "gold_evidence": r["evidence"]}
        for r in checker.testset()
    ])
    return dataset


def make_task(program: dspy.Module):
    def task(item: dict) -> dict:
        # Called inside evaluate(): this DSPy run becomes the trace linked to
        # the experiment item, with the module and LM spans nested below it.
        pred = program(fact_sheet=checker.FACT_SHEET, claim=item["claim"])
        return {"verdict": pred.verdict, "evidence": pred.evidence,
                "reasoning": pred.reasoning}
    return task


def run_experiment(dataset, program, name: str, compiled: bool):
    # evaluate() runs the task over every dataset item, applies the metrics,
    # and records one experiment: the row per claim and the score columns.
    return opik.evaluate(
        dataset=dataset,
        task=make_task(program),
        scoring_metrics=[DecisionCorrect(), EvidenceInHouseForm(), FullyCorrect()],
        experiment_name=name,
        experiment_config={
            "program": "ChainOfThought(CheckClaim)",
            "compiled": compiled,
            "optimizer": "BootstrapFewShot" if compiled else None,
            "demos": len(program.predict.demos),
            "model": checker.MODEL,
        },
        task_threads=4,
    )


def main() -> None:
    # OpikCallback turns every DSPy module and LM call into a trace: the
    # ChainOfThought/Predict spans, and a nested llm span with usage and
    # cost. log_graph=True also stores the module graph on the trace.
    dspy.configure(
        lm=checker.make_lm(),
        callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)],
    )
    client = opik.Opik()
    dataset = build_dataset(client)

    program = checker.build_program()
    print("Evaluating the uncompiled program...")
    before = run_experiment(dataset, program, "dspy-uncompiled", compiled=False)

    print("Compiling with BootstrapFewShot...")
    compiled = checker.compile_program(program)
    print("Evaluating the compiled program on the same dataset...")
    after = run_experiment(dataset, compiled, "dspy-compiled", compiled=True)

    print("\n=== Uncompiled vs compiled (mean over 12 claims) ===")
    for label, result in (("uncompiled", before), ("compiled  ", after)):
        stats = result.aggregate_evaluation_scores().aggregated_scores
        row = "  ".join(f"{k}={stats[k].mean:.2f}" for k in sorted(stats))
        print(f"{label}: {row}")
    print(f"\nCompare the runs: {after.experiment_url}")

    # Traces and experiment items ship from background threads; flush so
    # nothing is lost when the process exits.
    client.flush()
    opik.flush_tracker()


if __name__ == "__main__":
    main()
