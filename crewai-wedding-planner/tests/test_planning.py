import planning
from cost_report import split_by_agent


def test_fitting_venues_filters_and_sorts():
    fits = planning.fitting_venues(planning.load_venues(), 85)
    assert [v["name"] for v in fits] == ["Saltmarsh Pavilion", "Lantern Hollow Barn", "Old Mill Atrium"]
    assert all(v["capacity"] >= 85 for v in fits)
    assert [v["rental_usd"] for v in fits] == sorted(v["rental_usd"] for v in fits)


def test_vendor_total_mixes_per_guest_and_flat():
    vendors = planning.load_vendors()
    total = planning.vendor_total(vendors, {"catering": "Brightside Kitchen", "music": "DJ Orbit"}, 85)
    assert total == 54 * 85 + 1300


def test_formatters_name_every_item():
    text = planning.format_vendors(planning.load_vendors())
    assert "Marrow & Thyme: $78/guest" in text
    assert "Lantern Hollow Barn: restored timber barn, up to 140 guests, $6,800 rental." in planning.format_venues(planning.load_venues())


def test_split_by_agent_rolls_llm_cost_up_to_agent():
    spans = [
        {"id": "k", "parent_id": None, "name": "kickoff", "type": "general"},
        {"id": "t1", "parent_id": "k", "name": "Task: A", "type": "general"},
        {"id": "a1", "parent_id": "t1", "name": "Scout", "type": "general"},
        {"id": "f1", "parent_id": "a1", "name": "step", "type": "general"},
        {"id": "l1", "parent_id": "f1", "name": "chat_completion_create", "type": "llm", "tokens": 10, "cost": 0.5},
        {"id": "t2", "parent_id": "k", "name": "Task: B", "type": "general"},
        {"id": "a2", "parent_id": "t2", "name": "Budget", "type": "general"},
        {"id": "l2", "parent_id": "a2", "name": "chat_completion_create", "type": "llm", "tokens": 4, "cost": 0.25},
        {"id": "l3", "parent_id": "a2", "name": "chat_completion_create", "type": "llm", "tokens": 6, "cost": 0.25},
    ]
    out = split_by_agent(spans)
    assert out["Scout"] == {"calls": 1, "tokens": 10, "cost": 0.5}
    assert out["Budget"] == {"calls": 2, "tokens": 10, "cost": 0.5}


def test_traced_crew_inputs_work_with_tracking_disabled():
    # Importing main runs track_crewai; with OPIK_TRACK_DISABLE=true it must stay inert.
    import main

    data = main.inputs()
    assert set(data) == {"couple", "venues", "vendors"}
    assert "Marisol" in data["couple"]
