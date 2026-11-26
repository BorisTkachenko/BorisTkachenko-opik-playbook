"""Command line: `python -m trailclass <command>`."""

import argparse

from .config import load_env
from .data import load_split
from .prompts import BASELINE_SYSTEM


def cmd_baseline(_: argparse.Namespace) -> None:
    from .evaluate import accuracy

    for split in ("train", "validation"):
        score, results = accuracy(BASELINE_SYSTEM, load_split(split))
        print(f"baseline {split:<10} accuracy {score:.3f}  ({sum(r['ok'] for r in results)}/{len(results)})")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="trailclass", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline", help="score the starting prompt on train and validation").set_defaults(func=cmd_baseline)
    args = parser.parse_args(argv)
    load_env()
    args.func(args)
