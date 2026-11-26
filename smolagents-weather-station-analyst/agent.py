"""The weather-station analyst: a smolagents CodeAgent that answers by writing pandas."""

from pathlib import Path

from smolagents import CodeAgent, OpenAIServerModel

CSV_PATH = Path(__file__).parent / "data" / "readings.csv"

BRIEFING = f"""\
You are a data analyst for the Kestrel Ridge weather network.
The hourly readings are in the CSV file at: {CSV_PATH}

Columns: station, timestamp (YYYY-MM-DD HH:MM), temp_c, humidity_pct,
wind_kmh, rain_mm (rain in that hour), pressure_hpa.
There are five stations and three weeks of data. Sensors sometimes drop out:
those hours are blank cells (NaN once loaded), not zeros.

Load the file with pandas and answer with concrete numbers computed from it.
Give your final answer as one or two plain sentences, numbers rounded to one
decimal, not as a raw Python object.
"""

QUESTIONS = [
    "Which station and calendar day had the highest average wind speed "
    "(mean of wind_kmh over that day)? Give the station, date and the value.",
    "What is the total rainfall in mm for each station over the whole period?",
    "Which station had the longest dry spell, meaning the most consecutive "
    "calendar days with 0.0 mm total rain? Give the station, the number of "
    "days and the first and last date.",
]


def build_agent(model_id: str = "gpt-4o-mini") -> CodeAgent:
    """A CodeAgent writes Python and runs it; only pandas is authorized beyond
    smolagents' safe defaults, so the generated code can load the CSV and nothing else."""
    return CodeAgent(
        tools=[],
        model=OpenAIServerModel(model_id=model_id),
        additional_authorized_imports=["pandas"],
        max_steps=6,
    )


def ask(agent: CodeAgent, question: str) -> str:
    return str(agent.run(BRIEFING + "\nQuestion: " + question))
