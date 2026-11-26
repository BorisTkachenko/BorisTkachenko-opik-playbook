"""Paths, project name and Opik/OpenAI environment setup, shared by every module."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "openai-vision-nutrition-labels"
MODEL = "gpt-4o-mini"

# Example folder = two levels above src/nutrilabel/.
ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "products.json"
LABELS_DIR = ROOT / "labels"


def load_env() -> None:
    """Load .env files (repo root, then the example folder) and pin the Opik project."""
    for folder in [ROOT, *ROOT.parents]:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env")
    # An inherited OPENAI_BASE_URL would send calls somewhere other than OpenAI.
    os.environ.pop("OPENAI_BASE_URL", None)
    # Opik reads the project name from this variable: without it, traces from the
    # decorator and the OpenAI wrapper land in "Default Project".
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
