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
    raise SystemExit("The rule-level suite arrives with the evaluation layer.")


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
