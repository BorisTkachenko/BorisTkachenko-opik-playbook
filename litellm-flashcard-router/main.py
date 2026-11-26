"""Generate language-learning flashcards with two models through LiteLLM.

The same vocabulary list goes to a cheap OpenAI model and a cheap Anthropic
model; the script prints one comparison table (cards, tokens, cost, latency).
"""

import json
import logging
import os
import statistics
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (keys), walking up from this folder.
for parent in Path(__file__).resolve().parents:
    if (parent / ".env").exists():
        load_dotenv(parent / ".env")
        break

# Some dev environments point Anthropic traffic at a local proxy; LiteLLM must reach the real API.
os.environ.pop("ANTHROPIC_BASE_URL", None)

# Pin the Opik project before the callback is created, so traces never land in "Default Project".
PROJECT = "litellm-flashcard-router"
os.environ["OPIK_PROJECT_NAME"] = PROJECT

import litellm  # noqa: E402
import opik  # noqa: E402
from litellm.integrations.opik.opik import OpikLogger  # noqa: E402
from opik import opik_context  # noqa: E402

from flashcards import build_messages, parse_card  # noqa: E402

# OpikLogger is LiteLLM's callback: every litellm.completion() becomes an llm span
# carrying model, provider, token usage and cost, for both OpenAI and Anthropic.
# Built outside an event loop, OpikLogger logs a scary-looking (harmless) "no running event loop"
# error and falls back to synchronous sending; hide only that noise.
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
litellm.callbacks = [OpikLogger()]
logging.getLogger("LiteLLM").setLevel(logging.WARNING)

MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5-20251001",
]
VOCAB_PATH = Path(__file__).parent / "data" / "vocab.json"


# @opik.track opens one trace per (model, word) with a general span; the LiteLLM llm span nests under it.
@opik.track(name="make_card", project_name=PROJECT)
def make_card(model: str, entry: dict) -> dict:
    """One completion for one word. Returns the card plus latency, cost and tokens."""
    # Tags make "filter by model" possible in the traces table.
    opik_context.update_current_trace(tags=[model.split("/")[-1]])
    start = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=build_messages(entry),
        temperature=0.2,
        # Without current_span_data the callback cannot see the surrounding @track span and
        # logs the llm span as its own orphan trace instead of a child of make_card.
        metadata={"opik": {
            "current_span_data": opik_context.get_current_span_data(),
            "tags": [model.split("/")[-1]],
        }},
    )
    latency = time.perf_counter() - start
    return {
        "word": entry["word"],
        "card": parse_card(response.choices[0].message.content or ""),
        "latency": latency,
        "cost": response._hidden_params.get("response_cost") or 0.0,
        "tokens": response.usage.total_tokens,
    }


def summarize(results: dict[str, list[dict]]) -> list[dict]:
    """Collapse per-call results into one row per model."""
    rows = []
    for model, runs in results.items():
        rows.append({
            "model": model.split("/")[-1],
            "cards": f"{sum(r['card'] is not None for r in runs)}/{len(runs)}",
            "tokens": sum(r["tokens"] for r in runs),
            "cost": sum(r["cost"] for r in runs),
            "mean_latency": statistics.mean(r["latency"] for r in runs),
        })
    return rows


def print_table(rows: list[dict]) -> None:
    print(f"\n{'Model':<30} {'Valid cards':>11} {'Tokens':>7} {'Total cost':>11} {'Mean latency':>13}")
    print("-" * 76)
    for r in rows:
        print(f"{r['model']:<30} {r['cards']:>11} {r['tokens']:>7} "
              f"${r['cost']:>10.6f} {r['mean_latency']:>12.2f}s")


def main() -> None:
    vocab = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    results: dict[str, list[dict]] = {m: [] for m in MODELS}
    for model in MODELS:
        print(f"\n=== {model} ===")
        for entry in vocab:
            run = make_card(model, entry)
            results[model].append(run)
            card = run["card"]
            print(f"  {entry['word']:<13} {card['back'] if card else 'INVALID JSON'}")
    print_table(summarize(results))
    # Spans are sent from a background thread; flush so a short script does not exit before they arrive.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
