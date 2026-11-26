from datetime import datetime, timedelta
from types import SimpleNamespace

from check_opik import rows_from_spans
from report import format_table, summarize


def run(cost, latency, card=True, tokens=100):
    return {"card": {"front": "x"} if card else None, "cost": cost, "latency": latency, "tokens": tokens}


def test_summarize_totals_per_model():
    rows = summarize({"openai/a": [run(0.001, 1.0), run(0.001, 3.0, card=False)], "anthropic/b": [run(0.01, 2.0)]})
    assert rows[0]["model"] == "a" and rows[0]["ok"] == 1 and rows[0]["calls"] == 2
    assert rows[0]["cost"] == 0.002 and rows[0]["mean_latency"] == 2.0 and rows[0]["tokens"] == 200


def test_table_shows_ratio_to_cheapest():
    table = format_table(summarize({"openai/a": [run(0.001, 1.0)], "anthropic/b": [run(0.005, 1.0)]}))
    assert "1.0x" in table and "5.0x" in table


def test_rows_from_spans_counts_null_cost():
    t0 = datetime(2026, 1, 1)
    def span(model, cost):
        return SimpleNamespace(type="llm", model=model, total_estimated_cost=cost, usage={"total_tokens": 10},
                               start_time=t0, end_time=t0 + timedelta(seconds=2))
    rows, null_cost = rows_from_spans([span("m1", 0.1), span("m2", None), SimpleNamespace(type="general")])
    assert [r["model"] for r in rows] == ["m1", "m2"] and null_cost == 1
    assert rows[0]["mean_latency"] == 2.0
