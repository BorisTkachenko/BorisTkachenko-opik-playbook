"""Insurance-claims triage on the OpenAI Agents SDK.

A triage agent reads a claimant's message and hands off to an auto-damage,
property-damage or fraud-review specialist. Specialists call tools over the
fictional policy and claim files in data/. The demo plays three scripted
conversations, two of them with a follow-up turn.
"""

import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# Pin the Opik project before opik is imported, so traces never fall into "Default Project".
os.environ.setdefault("OPIK_PROJECT_NAME", "openai-agents-insurance-claims")

import opik
from agents import Agent, Runner, function_tool, set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

import claims_data

# Replaces the SDK's default OpenAI-dashboard exporter: every agent run now streams to Opik as a
# trace, with agent / handoff / tool / llm spans nested as a tree.
set_trace_processors(processors=[OpikTracingProcessor()])

MODEL = os.environ.get("CLAIMS_MODEL", "gpt-4o-mini")


@function_tool
def lookup_claim(claim_id: str) -> str:
    """Fetch a claim record (description, repair estimate, police report, prior claims)."""
    return json.dumps(claims_data.get_claim(claim_id))


@function_tool
def lookup_policy(policy_id: str) -> str:
    """Fetch a policy record (status, deductible, coverage limit, exclusions)."""
    return json.dumps(claims_data.get_policy(policy_id))


@function_tool
def estimate_payout(claim_id: str) -> str:
    """Compute the payout for a claim after deductible, limits and exclusions."""
    return json.dumps(claims_data.estimate_payout(claim_id))


@function_tool
def fraud_signals(claim_id: str) -> str:
    """List the fraud indicators recorded for a claim and an overall risk level."""
    return json.dumps(claims_data.get_fraud_signals(claim_id))


@function_tool
def refer_to_siu(claim_id: str, reason: str) -> str:
    """Refer a claim to the Special Investigations Unit with a short reason."""
    return json.dumps(claims_data.refer_to_siu(claim_id, reason))


auto_agent = Agent(
    name="Auto Damage Agent",
    handoff_description="Vehicle collision, theft and repair claims.",
    instructions=(
        "You handle auto claims. Look up the claim and its policy, then use "
        "estimate_payout and report the payout in one or two sentences. If the "
        "policy is not active say so plainly. Keep replies short."
    ),
    model=MODEL,
    tools=[lookup_claim, lookup_policy, estimate_payout],
)

property_agent = Agent(
    name="Property Damage Agent",
    handoff_description="Home damage claims: water, storm, fire.",
    instructions=(
        "You handle home claims. Look up the claim and its policy, check the "
        "exclusions, then use estimate_payout and report the result in one or "
        "two sentences, naming any exclusion that applies. Keep replies short."
    ),
    model=MODEL,
    tools=[lookup_claim, lookup_policy, estimate_payout],
)

fraud_agent = Agent(
    name="Fraud Review Agent",
    handoff_description="Claims that look suspicious or that the user asks to have reviewed for fraud.",
    instructions=(
        "You review claims for fraud. Call fraud_signals. If the risk is high, "
        "call refer_to_siu with a one-line reason; otherwise say no referral is "
        "needed. Keep replies short."
    ),
    model=MODEL,
    tools=[fraud_signals, refer_to_siu],
)

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "You are the intake desk of a home and auto insurer. Route the "
        "message to exactly one specialist: vehicle claims to the Auto Damage "
        "Agent, house claims to the Property Damage Agent, and anything where "
        "the user asks about fraud or suspicious circumstances to the Fraud "
        "Review Agent. Never answer claim questions yourself."
    ),
    model=MODEL,
    handoffs=[auto_agent, property_agent, fraud_agent],
)

DEMO_CONVERSATIONS = {
    "rear-end-collision": [
        "Hi, I'm Marta Lindqvist. Claim CLM-2001, I was rear-ended last week. How much will I get?",
        "Does my policy include a rental car while the repairs happen?",
    ],
    "burst-hose": [
        "Claim CLM-2002: a washing machine hose burst and flooded my kitchen. What will you pay?",
    ],
    "overnight-hit-and-run": [
        "Claim CLM-2003 says my car was hit overnight. Can you check whether the details look suspicious?",
        "Thanks. Setting the fraud question aside, what would CLM-2003 pay as a plain auto claim?",
    ],
}


def run_demo() -> None:
    for name, turns in DEMO_CONVERSATIONS.items():
        thread_id = f"{name}-{uuid.uuid4().hex[:8]}"
        print(f"\n=== {name} ({thread_id}) ===")
        history: list = []
        for message in turns:
            print(f"\nClaimant: {message}")
            history.append({"role": "user", "content": message})
            # One SDK trace per turn. The shared group_id becomes the Opik thread_id, so the
            # Threads tab stitches a claimant's turns into one conversation.
            with trace(workflow_name="Claims triage", group_id=thread_id):
                result = Runner.run_sync(triage_agent, history)
            print(f"Agent ({result.last_agent.name}): {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    try:
        run_demo()
    finally:
        # Traces are sent from a background thread; flush so a short script doesn't exit with spans unsent.
        opik.flush_tracker()
