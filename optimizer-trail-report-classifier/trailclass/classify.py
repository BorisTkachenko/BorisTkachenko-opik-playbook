"""Classify one trail report with an OpenAI chat model."""

import functools

import openai
import opik
from opik.integrations.openai import track_openai

from .config import MODEL, PROJECT_NAME
from .prompts import USER_TEMPLATE


@functools.cache
def _client() -> openai.OpenAI:
    # Built lazily so importing this module (tests) needs no API key.
    # track_openai wraps the client: every completion becomes an llm span in the
    # project, with the prompt, the reply, token usage and estimated cost.
    return track_openai(openai.OpenAI(), project_name=PROJECT_NAME)


# @opik.track opens one trace per report: a general span holding the report and
# the raw category, with the llm span from track_openai nested under it.
@opik.track(name="classify_report", project_name=PROJECT_NAME)
def classify(system_prompt: str, report: str) -> str:
    """Ask the model for a category; returns the raw reply text."""
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_TEMPLATE.format(report=report)},
        ],
    )
    return response.choices[0].message.content or ""
