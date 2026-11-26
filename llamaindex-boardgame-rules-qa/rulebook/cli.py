"""`rulebook build | ask | suite`."""

import argparse

from rulebook import tracing
from rulebook.config import load_env

DEMO_QUESTIONS = [
    "In Lanternfall, what are the three steps of a turn, and in what order?",
    "In Saltmarsh Couriers, what happens when the draw deck runs out for the second time?",
    "In Quillfire Duel, how much damage does a triple flare deal?",
    "Two Lanternfall players tie on points. Who wins?",
]


def cmd_build(_args) -> None:
    from rulebook.index.build import build_index

    index = build_index()
    print(f"Indexed {len(index.docstore.docs)} chunks from the rulebook PDFs into storage/.")


def cmd_ask(args) -> None:
    from rulebook.index.build import load_index
    from rulebook.qa.engine import ask, make_engine

    tracing.enable_tracing()
    engine = make_engine(load_index())
    for question in ([args.question] if args.question else DEMO_QUESTIONS):
        result = ask(engine, question)
        print(f"Q: {question}\nA: {result['answer']}\n")
    tracing.flush()


def cmd_suite(_args) -> None:
    from rulebook.index.build import load_index
    from rulebook.qa.engine import make_engine
    from rulebook.suite.run import run_suite

    tracing.enable_tracing()
    result = run_suite(make_engine(load_index()))
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items passed)")
    for item_result in result.item_results.values():
        runs = item_result.test_results
        out = runs[0].test_case.task_output
        status = "PASS" if item_result.passed else "FAIL"
        cites = sum(r.test_case.task_output["output"]["citation_ok"] for r in runs)
        print(f"  [{status}] {out['input']['question']}  (citation ok in {cites}/{len(runs)} runs)")
        if not item_result.passed:
            for run in runs:
                for score in run.score_results:
                    if score.scoring_failed or score.value != 1:
                        print(f"         failed: {score.name} - {score.reason}")
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")
    tracing.flush()


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(prog="rulebook")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="generate the PDFs if needed and index them").set_defaults(fn=cmd_build)
    ask_p = sub.add_parser("ask", help="answer one question (default: four demo questions)")
    ask_p.add_argument("question", nargs="?")
    ask_p.set_defaults(fn=cmd_ask)
    sub.add_parser("suite", help="run the rule-level test suite").set_defaults(fn=cmd_suite)
    args = parser.parse_args()
    args.fn(args)
