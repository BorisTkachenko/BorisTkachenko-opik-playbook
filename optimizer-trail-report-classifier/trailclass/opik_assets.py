"""Datasets and prompt-library entries this example keeps in Opik."""

import opik

from .config import LIBRARY_PROMPT, PROJECT_NAME
from .prompts import USER_TEMPLATE


def upload_dataset(client: opik.Opik, name: str, rows: list[dict], description: str) -> opik.Dataset:
    """Create (or reuse) a dataset and insert the rows.

    Opik deduplicates identical rows, so re-running does not grow it. Note that
    get_or_create_dataset ignores a changed description on an existing dataset.
    """
    dataset = client.get_or_create_dataset(name=name, description=description)
    dataset.insert(rows)
    return dataset


def to_mustache(text: str) -> str:
    """The optimizer fills {report}; the prompt library's template syntax is {{report}}."""
    return text.replace("{report}", "{{report}}")


def save_prompt_version(client: opik.Opik, system: str, change_description: str) -> opik.Prompt:
    """Save a system+user chat prompt to the Opik prompt library.

    Saving text that differs from the latest version creates a NEW version of the
    same prompt, so the library shows the baseline and its optimized successors
    side by side under Prompt library > trail-report-classifier.
    """
    return client.create_chat_prompt(
        name=LIBRARY_PROMPT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": to_mustache(USER_TEMPLATE)},
        ],
        change_description=change_description,
        project_name=PROJECT_NAME,
    )
