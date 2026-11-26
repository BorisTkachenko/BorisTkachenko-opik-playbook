"""Run the bounded optimization and hand the winner to `publish`."""

import json

import opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer

from .config import MAX_TRIALS, OPTIMIZER_MODEL, PROJECT_NAME, STATE_FILE
from .links import optimization_link
from .metric import trail_report_accuracy
from .prompts import BASELINE_SYSTEM, USER_TEMPLATE


def run_optimization(client: opik.Opik, train: opik.Dataset, n_train: int) -> dict:
    prompt = ChatPrompt(name="trail-report-classifier", system=BASELINE_SYSTEM, user=USER_TEMPLATE, model=OPTIMIZER_MODEL)
    optimizer = MetaPromptOptimizer(model=OPTIMIZER_MODEL, prompts_per_round=3, seed=42, verbose=1)
    # optimize_prompt creates an Opik optimization run: each trial is an experiment
    # on the train dataset, and the run page plots the score across trials.
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=train,
        metric=trail_report_accuracy,
        n_samples=n_train,  # score every training report on every trial
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,
    )
    messages = result.prompt.get_messages()
    state = {
        "system": next(m["content"] for m in messages if m["role"] == "system"),
        "initial_score": result.initial_score,
        "score": result.score,
        "trials": result.details.get("trials_completed"),
        "llm_calls": result.llm_calls,
        "llm_cost": result.llm_cost_total,
        "optimization_id": result.optimization_id,
        "link": optimization_link(client, result.optimization_id),
    }
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state
