"""Per-model comparison rows and the table both the app and the Opik check print (pure, no I/O)."""

import statistics


def summarize(results: dict[str, list[dict]]) -> list[dict]:
    """Collapse per-call results (latency, cost, tokens, card) into one row per model."""
    rows = []
    for model, runs in results.items():
        rows.append({
            "model": model.split("/")[-1],
            "ok": sum(r["card"] is not None for r in runs),
            "calls": len(runs),
            "tokens": sum(r["tokens"] for r in runs),
            "cost": sum(r["cost"] for r in runs),
            "mean_latency": statistics.mean(r["latency"] for r in runs),
        })
    return rows


def format_table(rows: list[dict]) -> str:
    """Render rows as one table, with each model's cost relative to the cheapest."""
    cheapest = min((r["cost"] for r in rows if r["cost"] > 0), default=0.0)
    lines = [
        f"{'Model':<28} {'Valid':>6} {'Tokens':>7} {'Total cost':>11} {'$/card':>10} "
        f"{'vs cheapest':>12} {'Mean latency':>13}",
        "-" * 94,
    ]
    for r in rows:
        ratio = f"{r['cost'] / cheapest:.1f}x" if cheapest and r["cost"] else "n/a"
        lines.append(
            f"{r['model']:<28} {str(r['ok']) + '/' + str(r['calls']):>6} {r['tokens']:>7} "
            f"${r['cost']:>10.6f} ${r['cost'] / r['calls']:>9.6f} {ratio:>12} "
            f"{r['mean_latency']:>12.2f}s"
        )
    return "\n".join(lines)
