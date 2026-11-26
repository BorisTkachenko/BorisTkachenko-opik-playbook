"""Run the bounded optimization and hand the winner to `publish`."""

import json
import re

import opik
from opik_optimizer import ChatPrompt, HierarchicalReflectiveOptimizer

from .config import MAX_TRIALS, OPTIMIZER_MODEL, PROJECT_NAME, RESPONSE_FORMAT, STATE_FILE
from .links import optimization_link
from .metric import trail_report_accuracy
from .prompts import BASELINE_SYSTEM, USER_TEMPLATE


def strip_placeholder(system: str) -> str:
    """Remove a stray {report} the optimizer may have written into the SYSTEM text.

    The report belongs in the user message. A rewrite that pastes the placeholder
    into the system prompt would otherwise be published (and scored) with the
    literal text "{report}" in it.
    """
    return re.sub(r"[:\s]*\{report\}", "", system).strip()


def run_optimization(client: opik.Opik, train: opik.Dataset, n_train: int) -> dict:
    prompt = ChatPrompt(
        name="trail-report-classifier",
        system=BASELINE_SYSTEM,
        user=USER_TEMPLATE,
        model=OPTIMIZER_MODEL,
        # Same enum-constrained reply as the app's classifier, so a candidate prompt can
        # only be scored on which category it picks, never on how it words the answer.
        model_kwargs={"response_format": RESPONSE_FORMAT},
    )
    optimizer = HierarchicalReflectiveOptimizer(
        model=OPTIMIZER_MODEL,
        reasoning_model=OPTIMIZER_MODEL,  # reads the failures and proposes the rewrite
        batch_size=12,
        seed=42,
        verbose=1,
    )
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
        "system": strip_placeholder(next(m["content"] for m in messages if m["role"] == "system")),
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
