"""Shared constants and environment loading."""

import os
import pathlib

import dotenv

PROJECT_NAME = "optimizer-trail-report-classifier"
MODEL = "gpt-4o-mini"
OPTIMIZER_MODEL = "openai/gpt-4o-mini"  # LiteLLM naming, used by the optimizer for task and reasoning
MAX_TRIALS = 6  # candidate prompts the optimizer may score: the budget cap
TRAIN_DATASET = "trail-reports-train"
VALIDATION_DATASET = "trail-reports-validation"
LIBRARY_PROMPT = "trail-report-classifier"
STATE_FILE = pathlib.Path(__file__).parents[1] / ".state" / "winner.json"
# Every trace this app emits goes to this Opik project; without it they would
# land in "Default Project". Set before opik is imported anywhere.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
DATA_DIR = pathlib.Path(__file__).parents[1] / "data"

LABELS = (
    "trail_hazard",
    "wildlife_sighting",
    "facility_issue",
    "lost_and_found",
    "compliment",
    "other",
)


def load_env() -> None:
    """Load the nearest .env found walking up from this folder (repo root or here)."""
    for folder in pathlib.Path(__file__).resolve().parents:
        candidate = folder / ".env"
        if candidate.is_file():
            dotenv.load_dotenv(candidate)
            return
