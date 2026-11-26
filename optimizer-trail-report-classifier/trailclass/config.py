"""Shared constants and environment loading."""

import os
import pathlib

import dotenv

PROJECT_NAME = "optimizer-trail-report-classifier"
MODEL = "gpt-4o-mini"
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
