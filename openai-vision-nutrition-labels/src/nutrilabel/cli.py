"""Command line entry point: `nutrilabel render | extract | suite`."""

import argparse
import json
import sys
from pathlib import Path

import opik

from .config import LABELS_DIR, MODEL, load_env
from .render import render_all


def cmd_render(_: argparse.Namespace) -> int:
    paths = render_all()
    print(f"Rendered {len(paths)} label images into {LABELS_DIR}")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    from .extract import extract_label

    load_env()
    if not args.images:
        render_all()
    images = args.images or sorted(str(p) for p in LABELS_DIR.glob("*.png"))
    print(f"Extracting {len(images)} labels with {MODEL}...\n")
    for image in images:
        print(f"{Path(image).name}\n  {json.dumps(extract_label(image))}\n")
    # Traces are sent in the background; flush so the short-lived CLI doesn't exit first.
    opik.flush_tracker()
    return 0


def cmd_suite(_: argparse.Namespace) -> int:
    from .suite import run_suite

    load_env()
    render_all()
    result = run_suite()
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} labels)")
    for item_result in result.item_results.values():
        image = Path(item_result.test_results[0].test_case.task_output["input"]["image"]).name
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {image}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nutrilabel", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("render", help="draw the label PNGs with Pillow").set_defaults(func=cmd_render)
    ex = sub.add_parser("extract", help="extract fields from label images (all of them by default)")
    ex.add_argument("images", nargs="*", help="label PNG paths")
    ex.set_defaults(func=cmd_extract)
    sub.add_parser("suite", help="run the Opik test suite over every label").set_defaults(func=cmd_suite)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
