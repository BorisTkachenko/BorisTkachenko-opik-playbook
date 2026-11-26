"""Score a prompt on a dataset as an Opik experiment."""

import opik
from opik.evaluation import evaluate

from .classify import classify
from .metric import CategoryMatch


def run_experiment(dataset: opik.Dataset, system: str, experiment_name: str) -> float:
    """Classify every dataset row with `system` and return the mean accuracy.

    evaluate() creates an experiment: one row per dataset item with its output and
    category_match score, linked to the classify_report traces it produced.
    """

    def task(item: dict) -> dict:
        return {"output": classify(system, item["report"])}

    result = evaluate(
        dataset=dataset,
        task=task,
        scoring_metrics=[CategoryMatch()],
        experiment_name=experiment_name,
        task_threads=4,
        verbose=0,
    )
    scores = [
        s.value for test in result.test_results for s in test.score_results if s.name == "category_match"
    ]
    return sum(scores) / len(scores)
