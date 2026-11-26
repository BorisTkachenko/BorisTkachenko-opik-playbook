"""Read the demo's traces back from Opik and summarise them per conversation (thread).

Run with:  uv run --with opik python check_opik.py
It reads OPIK_URL_OVERRIDE / OPIK_WORKSPACE / OPIK_API_KEY from your shell or the repo-root .env.
"""

import os
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = "langflow-gym-assistant"


def load_dotenv() -> None:
    for folder in (Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                key, sep, value = line.partition("=")
                if sep and not line.lstrip().startswith("#") and value:
                    os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_dotenv()
    import opik  # imported after .env is loaded so the SDK sees the Opik settings

    client = opik.Opik(project_name=PROJECT)
    traces = client.search_traces(project_name=PROJECT, max_results=500)
    by_thread: dict[str, list] = defaultdict(list)
    for trace in traces:
        by_thread[trace.thread_id or "(no thread)"].append(trace)

    span_kinds: Counter = Counter()
    total_cost, llm_spans, priced = 0.0, 0, 0
    for trace in traces:
        for span in client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=100):
            span_kinds[(span.name, span.type)] += 1
            if span.type == "llm":
                llm_spans += 1
                if span.total_estimated_cost is not None:
                    priced += 1
                    total_cost += span.total_estimated_cost

    print(f"project {PROJECT}: {len(traces)} traces in {len(by_thread)} threads")
    for thread, items in sorted(by_thread.items()):
        print(f"  thread {thread}: {len(items)} turns")
    print("spans per kind:", dict(sorted(span_kinds.items())))
    print(f"llm spans: {llm_spans}, priced: {priced}, total estimated cost: ${total_cost:.4f}")


if __name__ == "__main__":
    main()
