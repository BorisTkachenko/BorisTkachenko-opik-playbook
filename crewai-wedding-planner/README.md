# crewai-wedding-planner

**Three CrewAI agents plan one wedding, and Opik tells you what each of them cost.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/crewai-1.15-FF5A50?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

A crew hands you a finished plan and a single bill. If the bill is bigger than you expected, which agent
ran it up? This example runs a venue scout, a budget planner and a timeline coordinator for a fictional
couple, traces the whole thing as one Opik trace, and then splits tokens and dollars per agent.

## What you'll build

A sequential CrewAI crew on `gpt-4o-mini`. Marisol and Teodor (85 guests, $38,000, one October Saturday,
two wheelchair users) are described in `data/couple.md`. The scout picks a venue from `data/venues.json`
(pre-filtered to those that hold 85 guests), the planner prices vendors from `data/vendors.json`, and the
coordinator writes the run-of-show. Everything is offline and fictional; only an OpenAI key is needed.
`track_crewai(...)` is the only tracing call, and `cost_report.py` reads the result back from Opik.

## See it in Opik

Open the `crewai-wedding-planner` project and the one trace named `kickoff` (one run = one trace).
In my verified run it had 49 spans: three `Task: ...` spans (`Choose the venue`, `Plan the budget`,
`Draft the timeline`), one agent span under each (`Venue Scout`, `Budget Planner`, `Timeline
Coordinator`), CrewAI's internal flow steps beneath those, and one `chat_completion_create` llm span per
agent. The trace total was 2,576 tokens and about $0.00079. The per-agent split from `cost_report.py`:

| agent | llm calls | tokens | cost (USD) |
|---|---|---|---|
| Timeline Coordinator | 1 | 1047 | 0.000310 |
| Budget Planner | 1 | 846 | 0.000250 |
| Venue Scout | 1 | 683 | 0.000231 |
| total | 3 | 2576 | 0.000791 |

The coordinator costs most because it reads both upstream answers. Open any llm span to see its model
(`gpt-4o-mini-2024-07-18`), token usage and estimated cost.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or use a repo-root `.env`, which `main.py` finds by
   walking up). For a local Opik stack set `OPIK_URL_OVERRIDE`/`OPIK_WORKSPACE` as in `.env.example`.
2. `uv sync`
3. `uv run main.py` (about two minutes)
4. `uv run cost_report.py` to print the per-agent table for the latest trace.
5. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Give only the Budget Planner `llm="gpt-4o"` and rerun; compare its row in the table.
- Change `GUESTS` in `main.py` to 130 and see which venues survive the filter and how the plan shifts.
- Add a fourth agent and task; `cost_report.py` picks it up with no changes.
- Open the Timeline Coordinator's llm span and check its output against the venue's notes (sunset limits,
  accessibility). Small models do drift.

## Gotchas we hit

- **Symptom:** the agent spans (`Venue Scout`, ...) and the `kickoff` span show no cost when read through the
  SDK (`total_estimated_cost` is `None`), even though the trace total is filled. **Cause:** cost lives on
  the `llm` spans only; the agent spans are plain `general` spans. **Fix:** roll the llm spans up to their
  agent by walking parents until the parent is a `Task: ...` span, as `split_by_agent` in `cost_report.py`
  does.
- **Symptom:** the crew exits before traces show up. **Cause:** Opik sends in the background. **Fix:**
  `opik.flush_tracker()` at the end of `main.py`.
- **Symptom:** `uv run pytest` cannot import `planning`. **Fix:** `pythonpath = ["."]` under
  `[tool.pytest.ini_options]`.

## How it's put together

- `main.py` - agents, tasks, crew, `track_crewai` and the flush.
- `planning.py` - loads and formats the offline data, filters venues by capacity, sums vendor prices.
- `cost_report.py` - reads the latest trace from Opik and prints tokens and cost per agent.
- `data/` - `couple.md`, `venues.json`, `vendors.json` (all fictional).
- `tests/test_planning.py` - data helpers, the per-agent roll-up, and a traced import with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
