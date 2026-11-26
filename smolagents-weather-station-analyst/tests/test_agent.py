from types import SimpleNamespace

import agent
from tracing import PROJECT_NAME


def test_questions_and_references_line_up():
    from truth import load, reference_answers

    assert len(agent.QUESTIONS) == len(reference_answers(load()))


def test_briefing_points_at_the_csv_and_warns_about_gaps():
    assert str(agent.CSV_PATH) in agent.BRIEFING
    assert "NaN" in agent.BRIEFING and agent.CSV_PATH.exists()


def test_ask_runs_the_agent_with_briefing_and_returns_text():
    # A stub agent: with tracking/tracing off, ask() is plain function plumbing.
    seen = []
    stub = SimpleNamespace(run=lambda prompt: seen.append(prompt) or 42)
    assert agent.ask(stub, "how windy?") == "42"
    assert seen[0].endswith("Question: how windy?") and "Kestrel Ridge" in seen[0]


def test_project_name_matches_folder():
    assert PROJECT_NAME == "smolagents-weather-station-analyst"
