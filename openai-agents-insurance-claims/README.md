# openai-agents-insurance-claims

*A claims desk made of agents: triage, hand off, look up the policy, and see every step as a span tree.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat)
![openai-agents](https://img.shields.io/badge/openai--agents-0.26-412991?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

When an automated claims desk tells a customer "you'll get $0", someone has to work out why. Was the claim routed to the wrong specialist? Did the policy lookup return a lapsed policy? Or did the model ignore a correct tool result? From the final reply alone you can't tell. This example is a small home-and-auto claims desk built on the OpenAI Agents SDK, traced with Opik so each of those questions has a visible answer.

## What you'll build

Four agents on `gpt-4o-mini`:

- **Triage Agent** only routes. It never answers claim questions.
- **Auto Damage Agent** and **Property Damage Agent** look up a claim and its policy, then call `estimate_payout` (repair estimate minus deductible, capped by the limit, zero for lapsed policies or excluded floods).
- **Fraud Review Agent** reads recorded fraud signals and calls `refer_to_siu` when the risk is high.

All data is fictional and offline: four policies, four claims and a fraud-signal table in `data/`. The payout and risk rules are plain Python in `claims_data.py`, so they're unit-testable without a model. The demo plays three claimant conversations, two with a follow-up turn, and every turn is routed from scratch by the triage agent.

## See it in Opik

Open the `openai-agents-insurance-claims` project. After one demo run it holds **5 traces** (one per turn), all named `Claims triage`, and **76 spans**.

Open the last trace of the overnight-hit-and-run conversation ("what would CLM-2003 pay as a plain auto claim?"). Expand the tree: a `Task` span contains a `Triage Agent` span, a `Handoff` span, then an `Auto Damage Agent` span. Under the specialist you'll see `lookup_claim`, `lookup_policy` and `estimate_payout` tool spans with their exact arguments and JSON results, and between them the `Response` spans (type `llm`) for each model turn. The `estimate_payout` span returns `payout_usd: 0` with reason `policy lapsed`, so you can see the "$0" came from the data, not from the model improvising.

Every `llm` span carries token usage and an estimated cost (21 of 21 priced against `gpt-4o-mini-2024-07-18`); a single turn costs between about $0.0002 and $0.0006.

Now switch to the **Threads** tab. You'll find three threads: `rear-end-collision-…`, `burst-hose-…` and `overnight-hit-and-run-…`, with 2, 1 and 2 traces. In the fraud conversation the first turn went to the Fraud Review Agent (`fraud_signals`, then `refer_to_siu`, case `SIU-001`) and the second to the Auto Damage Agent, and the thread shows both in order. That is the case for threads: a claimant asks about "my claim" across several turns, and you read the whole exchange rather than hunting for neighbouring traces.

## Run it yourself

1. `cd openai-agents-insurance-claims`
2. `cp .env.example .env`, then set `OPENAI_API_KEY` (a `.env` in the parent folder also works).
3. Point Opik at your instance: run `opik configure`, or set `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` (and `OPIK_API_KEY` for Comet cloud) in `.env`.
4. `uv sync`
5. `uv run main.py` (about 30 to 60 seconds, under a cent in model costs)
6. Open the project in Opik and click the newest trace.

Offline tests, no keys or network needed:
`env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Edit `data/policies.json` and set `POL-1001` to `"status": "lapsed"`. Re-run and find the `estimate_payout` span flip to zero, with the agent's reply following it.
- Reword a demo message so it is ambiguous ("my basement flooded and I think the neighbour's car caused it") and watch which way the `Handoff` span goes.
- Remove `group_id=thread_id` in `main.py` and compare the Threads tab: the turns scatter into separate traces.
- Add a fourth specialist (say, a travel-insurance agent) to `handoffs=[...]` and note that the new handoff appears with no tracing changes.

## Gotchas we hit

- **Symptom:** the follow-up turn of a conversation is answered by a different agent than the first. **Cause:** `Runner.run_sync(triage_agent, history)` restarts at the triage agent each turn, so each turn is re-routed (visible as a fresh `Handoff` span). **Fix:** that is the behaviour shown here; to continue with the same specialist, start the next run from `result.last_agent` instead.
- **Symptom:** traces land in "Default Project" or never appear. **Cause:** the project name is read when `opik` is first imported, and spans are sent from a background thread. **Fix:** set `os.environ["OPIK_PROJECT_NAME"]` before `import opik`, and finish the script with `opik.flush_tracker()`.
- **Symptom:** the Threads tab is empty although traces exist. **Cause:** the Agents SDK only forwards a thread id when a `trace(...)` block carries `group_id`. **Fix:** wrap each run in `with trace(workflow_name="Claims triage", group_id=thread_id):`.

## How it's put together

- `main.py` — agents, function tools, the Opik tracing processor, and the scripted demo conversations.
- `claims_data.py` — policy and claim lookups, payout rules, fraud risk levels and the SIU queue, with no model dependency.
- `data/` — fictional policies, claims and fraud signals.
- `tests/test_claims.py` — offline tests for payout math, exclusions, risk levels, and a check that the traced module imports and works with tracking disabled.
- `.env.example` — the variables the example reads.

---

*built with Opik · inspired by Opik's examples and documentation*
