"""Create (or update) the rule-level test suite in Opik and run it against the engine."""

import opik

from rulebook.config import PROJECT_NAME
from rulebook.qa.engine import ask
from rulebook.suite.checks import citation_ok
from rulebook.suite.items import CASES, GLOBAL_ASSERTIONS

SUITE_NAME = "boardgame-rules-suite"
# The judge is an LLM, so a single run per item is flaky: run each item 3 times and pass if 2 agree.
POLICY = {"runs_per_item": 3, "pass_threshold": 2}


def sync_suite(client: opik.Opik):
    # A test suite is a versioned dataset of items plus judge assertions; run_tests scores each
    # task output against them and records the run as an experiment in the project.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=list(GLOBAL_ASSERTIONS),
        global_execution_policy=POLICY,
    )
    # get_or_create ignores changed settings on an existing suite, so push them explicitly.
    suite.update_test_settings(global_assertions=list(GLOBAL_ASSERTIONS), global_execution_policy=POLICY)
    suite.insert([
        {"data": {"question": c.question, "game": c.game, "section": c.section},
         "assertions": list(c.assertions)}
        for c in CASES
    ])
    return suite


def run_suite(engine) -> opik.api_objects.dataset.test_suite.types.TestSuiteResult:
    client = opik.Opik(project_name=PROJECT_NAME)
    suite = sync_suite(client)

    def task(item: dict) -> dict:
        # The retrieved excerpts travel with the answer so the judge can check "only states
        # rules from the excerpts" against what retrieval really returned. The engine call
        # is also traced by the LlamaIndex handler, so each run has retrieve/synthesize spans.
        result = ask(engine, item["question"])
        return {
            "input": item,
            "output": {
                "answer": result["answer"],
                "retrieved_excerpts": [s["text"] for s in result["sources"]],
                "citation_ok": citation_ok(result["answer"], item["game"], item["section"]),
            },
        }

    return opik.run_tests(test_suite=suite, task=task, worker_threads=3, generate_report=False)
