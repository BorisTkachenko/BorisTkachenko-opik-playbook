"""Settings. Import this module before anything that imports opik."""

import os
import pathlib

import dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Walk up from the example folder to the first .env (the repo root holds one
# with the Opik settings). There is no model key to load: everything is local.
for folder in (ROOT, *ROOT.parents):
    if (folder / ".env").is_file():
        dotenv.load_dotenv(folder / ".env")
        break

PROJECT_NAME = "ollama-homebrew-rag"
# Opik reads the project from this variable; setting it before the first traced
# call keeps every trace out of "Default Project".
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = "llama3.2:1b"
EMBED_MODEL = "nomic-embed-text"

DOCS_DIR = ROOT / "docs"
INDEX_PATH = ROOT / ".index" / "index.json"
TOP_K = 2
