import os

os.environ["OPIK_TRACK_DISABLE"] = "true"  # keep unit tests off the network

import pytest

import claims_data
import main


def test_payout_is_estimate_minus_deductible():
    assert claims_data.estimate_payout("CLM-2001")["payout_usd"] == 2650


def test_lapsed_policy_pays_nothing():
    result = claims_data.estimate_payout("CLM-2003")
    assert result["payout_usd"] == 0 and "lapsed" in result["reason"]


def test_flood_exclusion():
    result = claims_data.estimate_payout("CLM-2004")
    assert result["payout_usd"] == 0 and "flood" in result["reason"]


def test_unknown_ids_return_errors():
    assert "error" in claims_data.get_claim("CLM-9999")
    assert "error" in claims_data.get_policy("POL-0")


def test_fraud_risk_levels():
    assert claims_data.get_fraud_signals("CLM-2001")["risk"] == "low"
    assert claims_data.get_fraud_signals("CLM-2004")["risk"] == "medium"
    assert claims_data.get_fraud_signals("CLM-2003")["risk"] == "high"


def test_siu_referral_numbers_cases():
    first = claims_data.refer_to_siu("CLM-2003", "lapsed policy")
    assert first["status"] == "referred" and first["case"].startswith("SIU-")


def test_agent_graph_and_traced_setup_import_cleanly():
    # Importing main installs OpikTracingProcessor; with tracking disabled it must not get in the way.
    assert [a.name for a in main.triage_agent.handoffs] == [
        "Auto Damage Agent", "Property Damage Agent", "Fraud Review Agent"]
    assert main.DEMO_CONVERSATIONS["overnight-hit-and-run"]
