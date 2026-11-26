"""Extract the sample posts, then run them as an Opik test suite."""

from typing import Any

import logfire
import opik

from checks import invented_fields, missed_fields
from listing_agent import MODEL, extract_listing, load_posts
from tracing import PROJECT_NAME

# Suite-level rules every extraction must satisfy, in plain language. Opik's LLM judge
# checks each one against the agent output for every item.
GLOBAL_ASSERTIONS = [
    "The output has the fields brand, model, mount, condition, price_usd, shutter_count, accessories and location",
    "Every non-null value is stated in, or directly derivable from, the post text",
    "A field the post does not state is null (an empty list for accessories); no value is guessed",
    "price_usd is only set when the post gives a price in US dollars",
]


def main() -> None:
    posts = load_posts()
    print(f"Extracting {len(posts)} posts with {MODEL}...\n")
    for post in posts:
        listing = extract_listing(post["text"])
        print(f"{post['id']:26} invented={invented_fields(listing, post['expected'])} "
              f"missed={missed_fields(listing, post['expected'])}")

    client = opik.Opik(project_name=PROJECT_NAME)
    # The suite stores items (just the post text) plus assertions. Expected values live only in
    # assertions, never in the item data, so the judge cannot read answers off the input.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        # Judges and models are noisy: run each item 3 times, pass if 2 pass.
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    suite.insert([{"data": {"text": p["text"]}, "assertions": p["assertions"]} for p in posts])

    def task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_listing(item["text"])}

    # run_tests creates one experiment: every item x run becomes a trace with judge verdicts attached.
    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=f"listing-extraction-{MODEL.split(':')[-1]}",
        worker_threads=4,
        generate_report=False,
    )
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items)")
    for r in result.item_results.values():
        text = r.test_results[0].test_case.task_output["input"]["text"]
        print(f"  [{'PASS' if r.passed else 'FAIL'}] {text[:64]!r}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Flush both exporters before exit, or the last spans never leave the process.
    logfire.force_flush()
    client.flush()


if __name__ == "__main__":
    main()
