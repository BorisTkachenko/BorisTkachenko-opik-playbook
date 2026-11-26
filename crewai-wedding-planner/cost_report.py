"""Per-agent token and cost split for the latest kickoff in Opik.

Run after main.py:  uv run cost_report.py
"""

import os
from collections import defaultdict

import opik

PROJECT = "crewai-wedding-planner"


def split_by_agent(spans: list[dict]) -> dict[str, dict]:
    """Roll llm-span cost and tokens up to the agent that made the calls.

    An agent span is the direct child of a "Task: ..." span. The agent spans themselves carry
    no cost, so each llm span is walked up its parents until an agent span is found.
    """
    by_id = {s["id"]: s for s in spans}

    def agent_of(span: dict) -> str | None:
        while span.get("parent_id"):
            parent = by_id.get(span["parent_id"])
            if parent is None:
                return None
            if parent["name"].startswith("Task: "):
                return span["name"]
            span = parent
        return None

    totals: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
    for s in spans:
        if s["type"] != "llm":
            continue
        agent = agent_of(s)
        if agent is None:
            continue
        t = totals[agent]
        t["calls"] += 1
        t["tokens"] += s.get("tokens") or 0
        t["cost"] += s.get("cost") or 0.0
    return dict(totals)


def latest_kickoff_spans(client: opik.Opik) -> list[dict]:
    # Read the newest trace back via the SDK; llm spans hold the usage and cost used below.
    traces = client.search_traces(project_name=PROJECT, max_results=50)
    trace = max(traces, key=lambda t: t.start_time)
    spans = client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=500)
    return [
        {
            "id": s.id,
            "parent_id": s.parent_span_id,
            "name": s.name,
            "type": s.type,
            "tokens": (s.usage or {}).get("total_tokens"),
            "cost": s.total_estimated_cost,
        }
        for s in spans
    ]


if __name__ == "__main__":
    client = opik.Opik()
    split = split_by_agent(latest_kickoff_spans(client))
    total = sum(v["cost"] for v in split.values())
    print(f"{'agent':<22}{'llm calls':>10}{'tokens':>9}{'cost (USD)':>13}")
    for agent, v in split.items():
        print(f"{agent:<22}{v['calls']:>10}{v['tokens']:>9}{v['cost']:>13.6f}")
    print(f"{'total':<22}{sum(v['calls'] for v in split.values()):>10}"
          f"{sum(v['tokens'] for v in split.values()):>9}{total:>13.6f}")
