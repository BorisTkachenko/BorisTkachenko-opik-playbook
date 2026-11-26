"""Command line: `python -m trailclass baseline | optimize | publish`."""

import argparse
import json

import opik

from .config import PROJECT_NAME, STATE_FILE, TRAIN_DATASET, VALIDATION_DATASET, load_env
from .data import load_split
from .prompts import BASELINE_SYSTEM


def _datasets(client: opik.Opik):
    from .opik_assets import upload_dataset

    train = upload_dataset(client, TRAIN_DATASET, load_split("train"), "Park trail reports the optimizer trains on")
    validation = upload_dataset(
        client, VALIDATION_DATASET, load_split("validation"), "Held-out trail reports the optimizer never sees"
    )
    return train, validation


def cmd_baseline(client: opik.Opik, _: argparse.Namespace) -> None:
    from .experiments import run_experiment
    from .opik_assets import save_prompt_version

    train, validation = _datasets(client)
    # Version 1 of the library prompt is the hand-written baseline.
    save_prompt_version(client, BASELINE_SYSTEM, {"source": "hand-written baseline"})
    for name, dataset in (("train", train), ("validation", validation)):
        score = run_experiment(dataset, BASELINE_SYSTEM, f"baseline-{name}")
        print(f"baseline {name:<10} accuracy {score:.3f}")


def cmd_optimize(client: opik.Opik, _: argparse.Namespace) -> None:
    from .config import MAX_TRIALS
    from .optimize import run_optimization

    train, _validation = _datasets(client)
    state = run_optimization(client, train, len(load_split("train")))
    print(f"\ntrain accuracy  {state['initial_score']:.3f} -> {state['score']:.3f}")
    print(f"trials          {state['trials']} (budget {MAX_TRIALS}), llm calls {state['llm_calls']}")
    cost = state["llm_cost"]
    print(f"optimizer cost  {'$%.4f' % cost if cost is not None else 'unavailable'}")
    print(f"optimization run {state['link']}")


def cmd_publish(client: opik.Opik, _: argparse.Namespace) -> None:
    from .experiments import run_experiment
    from .opik_assets import save_prompt_version
    from .publish import should_publish

    if not STATE_FILE.exists():
        raise SystemExit("No winner yet: run `python -m trailclass optimize` first.")
    state = json.loads(STATE_FILE.read_text())
    _train, validation = _datasets(client)
    # Held-out check: the optimizer never saw these reports.
    base = run_experiment(validation, BASELINE_SYSTEM, "baseline-validation-recheck")
    win = run_experiment(validation, state["system"], "winner-validation")
    print(f"validation accuracy  baseline {base:.3f}  winner {win:.3f}  ({win - base:+.3f})")
    if not should_publish(BASELINE_SYSTEM, state["system"], base, win):
        print("Winner did not clearly beat the baseline on held-out reports: nothing saved to the library.")
        return
    prompt = save_prompt_version(
        client,
        state["system"],
        {
            "source": "HierarchicalReflectiveOptimizer winner",
            "train_accuracy": f"{state['initial_score']:.3f} -> {state['score']:.3f}",
            "validation_accuracy": f"{base:.3f} -> {win:.3f}",
            "optimization_id": state["optimization_id"],
        },
    )
    print(f"Saved as a new version of '{prompt.name}' in the prompt library.\n\nWinning system prompt:\n")
    print(state["system"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="trailclass", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline", help="upload data, save prompt v1, score it on train and validation").set_defaults(func=cmd_baseline)
    sub.add_parser("optimize", help="run the bounded optimization on the train split").set_defaults(func=cmd_optimize)
    sub.add_parser("publish", help="check the winner on validation and save it to the prompt library").set_defaults(func=cmd_publish)
    args = parser.parse_args(argv)
    load_env()
    # The client owns datasets, prompt-library saves and the optimization run; pinning
    # project_name keeps all of them out of "Default Project".
    client = opik.Opik(project_name=PROJECT_NAME)
    try:
        args.func(client, args)
    finally:
        # Traces are sent from a background thread; flush so a short-lived CLI
        # run does not exit with spans still queued.
        opik.flush_tracker()
        client.flush()
