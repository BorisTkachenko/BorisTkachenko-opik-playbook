"""`ingest`, `ask` and a scripted `demo`."""

import argparse

from . import config  # first: sets the Opik project before opik is imported

import opik

from .answer import ask
from .ingest import build_index
from .retrieve import Index

DEMO_QUESTIONS = [
    "What temperature should I mash at for a fuller, sweeter body?",
    "When should I add hops at flameout and why?",
    "My beer tastes like butterscotch. What went wrong and how do I fix it?",
]


def _ask_and_print(question: str, index: Index) -> None:
    result = ask(question, index)
    print(f"Q: {question}\nA: {result['answer']}\n   sources: {', '.join(result['sources'])}\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="homebrew-rag")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="embed docs/ and write the local index")
    ask_p = sub.add_parser("ask", help="ask one question")
    ask_p.add_argument("question")
    sub.add_parser("demo", help="ingest, then answer three scripted questions")
    args = parser.parse_args(argv)

    if args.command in ("ingest", "demo"):
        print(build_index(config.DOCS_DIR, config.INDEX_PATH))
    if args.command == "ask":
        _ask_and_print(args.question, Index.load(config.INDEX_PATH))
    elif args.command == "demo":
        index = Index.load(config.INDEX_PATH)
        for question in DEMO_QUESTIONS:
            _ask_and_print(question, index)

    # Traces are sent from a background thread; without a flush the CLI can
    # exit before the last ones are delivered.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
