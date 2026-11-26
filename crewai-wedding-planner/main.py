"""Wedding-planner crew: venue scout, budget planner, timeline coordinator."""

from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (walking up from this folder) before crewai reads keys.
for parent in Path(__file__).resolve().parents:
    if (parent / ".env").exists():
        load_dotenv(parent / ".env")
        break

import opik
from crewai import Agent, Crew, Process, Task
from opik.integrations.crewai import track_crewai

import planning

MODEL = "gpt-4o-mini"
PROJECT = "crewai-wedding-planner"

venue_scout = Agent(
    role="Venue Scout",
    goal="Pick the one venue that fits the couple's guest list, access needs and budget.",
    backstory="A former events manager who has walked hundreds of venues and checks accessibility first.",
    llm=MODEL,
)

budget_planner = Agent(
    role="Budget Planner",
    goal="Build a line-item budget that stays under the couple's total.",
    backstory="A meticulous planner who never lets a plan exceed the budget and shows the arithmetic.",
    llm=MODEL,
)

timeline_coordinator = Agent(
    role="Timeline Coordinator",
    goal="Turn the venue and budget into an hour-by-hour wedding weekend schedule.",
    backstory="A calm coordinator who thinks in run-of-show sheets and builds in weather fallbacks.",
    llm=MODEL,
)

venue_task = Task(
    name="Choose the venue",
    description=(
        "Choose ONE venue for this couple using only the data below.\n\n"
        "COUPLE:\n{couple}\n\nVENUES (already filtered to fit the guest count):\n{venues}"
    ),
    expected_output="The chosen venue, three reasons, and one risk the couple should plan around.",
    agent=venue_scout,
)

budget_task = Task(
    name="Plan the budget",
    description=(
        "Using the chosen venue and ONLY the vendor price list below, pick vendors and write a "
        "line-item budget for the whole wedding. Show the total and the margin left.\n\n"
        "VENDORS:\n{vendors}"
    ),
    expected_output="A line-item budget table with a total under $38,000 and one sentence per vendor choice.",
    agent=budget_planner,
    context=[venue_task],
)

timeline_task = Task(
    name="Draft the timeline",
    description=(
        "Write the run-of-show for the wedding Saturday and the farewell brunch, based on the venue "
        "and budget. Respect the couple's end time and give the ceremony a weather fallback."
    ),
    expected_output="A timeline under 250 words with times, plus the fallback plan in one sentence.",
    agent=timeline_coordinator,
    context=[venue_task, budget_task],
)

crew = Crew(
    agents=[venue_scout, budget_planner, timeline_coordinator],
    tasks=[venue_task, budget_task, timeline_task],
    process=Process.sequential,
    verbose=True,
)

# track_crewai patches CrewAI and LiteLLM so one kickoff becomes ONE trace: a span per task and
# agent, with every LLM call logged as an llm span carrying model, token usage and cost.
track_crewai(project_name=PROJECT, crew=crew)

GUESTS = 85


def inputs() -> dict:
    return {
        "couple": planning.load_couple(),
        "venues": planning.format_venues(planning.fitting_venues(planning.load_venues(), GUESTS)),
        "vendors": planning.format_vendors(planning.load_vendors()),
    }


if __name__ == "__main__":
    result = crew.kickoff(inputs=inputs())
    print("\n=== WEDDING PLAN ===\n")
    print(result)
    # Traces are sent from a background thread; flush so a short script doesn't exit before they land.
    opik.flush_tracker()
