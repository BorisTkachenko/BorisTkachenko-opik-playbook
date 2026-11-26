"""Classify one trail report with an OpenAI chat model."""

import openai

from .config import MODEL
from .prompts import USER_TEMPLATE

_client = openai.OpenAI()


def classify(system_prompt: str, report: str) -> str:
    """Ask the model for a category; returns the raw reply text."""
    response = _client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_TEMPLATE.format(report=report)},
        ],
    )
    return response.choices[0].message.content or ""
