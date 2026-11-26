"""Offline claims data and the pure functions behind the agents' tools.

Everything here is plain Python over the fictional JSON files in data/, so the
payout math and lookups can be unit-tested without a model.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text())


def get_policy(policy_id: str) -> dict:
    for policy in _load("policies.json"):
        if policy["policy_id"].upper() == policy_id.strip().upper():
            return policy
    return {"error": f"unknown policy {policy_id}"}


def get_claim(claim_id: str) -> dict:
    for claim in _load("claims.json"):
        if claim["claim_id"].upper() == claim_id.strip().upper():
            return claim
    return {"error": f"unknown claim {claim_id}"}


def estimate_payout(claim_id: str) -> dict:
    """Repair estimate minus the deductible, capped at the coverage limit.

    A lapsed policy pays nothing; a flood loss on a policy without flood cover
    pays nothing.
    """
    claim = get_claim(claim_id)
    if "error" in claim:
        return claim
    policy = get_policy(claim["policy_id"])
    if policy["status"] != "active":
        return {"claim_id": claim_id, "payout_usd": 0, "reason": f"policy {policy['status']}"}
    if "flood" in claim["description"].lower() and not policy.get("flood", True):
        return {"claim_id": claim_id, "payout_usd": 0, "reason": "flood is excluded by this policy"}
    payout = min(max(claim["repair_estimate_usd"] - policy["deductible_usd"], 0),
                 policy["coverage_limit_usd"])
    return {"claim_id": claim_id, "payout_usd": payout,
            "reason": f"estimate {claim['repair_estimate_usd']} - deductible {policy['deductible_usd']}"}


def get_fraud_signals(claim_id: str) -> dict:
    signals = _load("fraud_signals.json").get(claim_id.strip().upper())
    if signals is None:
        return {"error": f"unknown claim {claim_id}"}
    risk = "low" if not signals else "medium" if len(signals) < 3 else "high"
    return {"claim_id": claim_id, "signals": signals, "risk": risk}


_SIU_QUEUE: list[dict] = []


def refer_to_siu(claim_id: str, reason: str) -> dict:
    """Queue a claim for the Special Investigations Unit (in-memory only)."""
    entry = {"claim_id": claim_id, "reason": reason, "case": f"SIU-{len(_SIU_QUEUE) + 1:03d}"}
    _SIU_QUEUE.append(entry)
    return {"status": "referred", **entry}
