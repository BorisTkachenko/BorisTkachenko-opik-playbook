"""A Pydantic AI agent that turns messy camera-marketplace posts into typed listings."""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import opik
from tracing import PROJECT_NAME, setup_tracing

MODEL_NAME = "gpt-4o-mini"
MODEL = f"openai:{MODEL_NAME}"
DATA_FILE = Path(__file__).parent / "data" / "posts.json"

# Keys come from the repo-root .env (walk up from this folder) or a local .env.
for parent in Path(__file__).resolve().parents:
    if (parent / ".env").exists():
        load_dotenv(parent / ".env")
        break


# Must run before the agent makes its first call so the OTLP exporter is configured.
setup_tracing()


class CameraListing(BaseModel):
    """What a post actually says. Anything the post does not state stays null."""

    brand: str | None = Field(None, description="Manufacturer, only if named")
    model: str | None = Field(None, description="Model name, only if named")
    mount: str | None = Field(None, description="Lens mount, only if stated")
    condition: str | None = Field(None, description="Seller's own condition wording")
    price_usd: float | None = Field(None, description="Asking price in US dollars, only if the post gives one in USD")
    shutter_count: int | None = Field(None, description="Shutter actuations, only if a number is given")
    accessories: list[str] = Field(default_factory=list, description="Items included in the sale")
    location: str | None = Field(None, description="Seller location, only if stated")


SYSTEM_PROMPT = (
    "You extract a CameraListing from a messy marketplace post. Copy only what "
    "the post states. If a field is not in the post, return null (an empty list "
    "for accessories). Never guess a brand, model, mount, price or count, and do "
    "not convert currencies. Use the check_mount tool to normalise a mount name "
    "when the post names one, then copy the mount into the listing as the post wrote it."
)

KNOWN_MOUNTS = {"m39", "k bayonet", "pl", "bayonet", "m42", "f mount"}

agent = Agent(MODEL, output_type=CameraListing, system_prompt=SYSTEM_PROMPT)


@agent.tool_plain
def check_mount(name: str) -> str:
    """Report whether a lens mount name is a mount this marketplace recognises."""
    known = name.strip().lower() in KNOWN_MOUNTS
    return f"{name!r} is {'a recognised' if known else 'not a recognised'} mount name"


# track opens the trace for this extraction (general span; the tracked function's input and
# output show on it). The Pydantic AI spans nest beneath it via OpikSpanProcessor.
@opik.track(project_name=PROJECT_NAME)
def extract_listing(text: str) -> dict[str, Any]:
    """One extraction: post text in, listing dict out."""
    # A fresh client per call: run_sync uses one event loop per thread, and a shared
    # cached HTTP client breaks with "bound to a different event loop" under run_tests' workers.
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=AsyncOpenAI()))
    return agent.run_sync(text, model=model).output.model_dump()


def load_posts() -> list[dict[str, Any]]:
    return json.loads(DATA_FILE.read_text())


def main() -> None:
    for post in load_posts():
        print(post["id"], "->", extract_listing(post["text"]))


if __name__ == "__main__":
    main()
