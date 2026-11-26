"""Paths, model names and environment loading shared by every module."""

import pathlib

import dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdfs"
STORAGE_DIR = ROOT / "storage"

PROJECT_NAME = "llamaindex-boardgame-rules-qa"
LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"


def load_env() -> None:
    """Load the nearest .env walking up from the example folder (repo root in a clone)."""
    for folder in (ROOT, *ROOT.parents):
        candidate = folder / ".env"
        if candidate.exists():
            dotenv.load_dotenv(candidate)
            return
