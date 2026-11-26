"""Ask the weather-station analyst three questions and print each answer."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Repo-root .env first (when cloned inside a larger repo), then a local one.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")
os.environ.pop("OPENAI_BASE_URL", None)  # always talk to the public OpenAI API

from agent import QUESTIONS, ask, build_agent  # noqa: E402
from truth import grade, load, reference_answers  # noqa: E402
from tracing import PROJECT_NAME, setup_tracing  # noqa: E402


def main() -> None:
    # Instrument BEFORE building the agent so its model and steps are patched.
    provider = setup_tracing()
    agent = build_agent()
    references = reference_answers(load())
    passed = 0
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'=' * 72}\nQuestion {i}: {question}\n{'=' * 72}")
        answer = ask(agent, question)
        reference, facts = references[i - 1]
        ok = grade(answer, facts)
        passed += ok
        print(f"\nAnswer {i}: {answer}\nReference: {reference}\nVerdict: {'MATCH' if ok else 'MISMATCH'}")

    # Flush and shut down the exporter so the last spans reach Opik before the process exits.
    provider.shutdown()
    print(f"\n{passed}/{len(QUESTIONS)} answers match the pandas reference.")
    print(f"Done. Open the '{PROJECT_NAME}' project in Opik: one trace per question.")


if __name__ == "__main__":
    main()
