import json

import pytest
from pydantic_ai.models.test import TestModel

from checks import invented_fields, missed_fields
from listing_agent import CameraListing, agent, check_mount, extract_listing, load_posts


def test_every_post_has_expected_values_and_assertions():
    for post in load_posts():
        assert post["text"] and post["assertions"]
        assert set(post["expected"]) == set(CameraListing.model_fields)


def test_corpus_includes_posts_that_omit_fields():
    # The point of the suite: some posts must leave fields empty, or "invented" has no meaning.
    assert sum(1 for p in load_posts() if p["expected"]["price_usd"] is None) >= 3


def test_invented_fields_flags_values_the_post_never_stated():
    expected = {"brand": None, "price_usd": None, "accessories": [], "mount": "M39"}
    listing = {"brand": "Kestrel", "price_usd": None, "accessories": ["strap"], "mount": "M39"}
    assert invented_fields(listing, expected) == ["brand", "accessories"]


def test_missed_fields_flags_stated_values_left_null():
    assert missed_fields({"mount": None}, {"mount": "M39"}) == ["mount"]


def test_check_mount_tool():
    assert "a recognised" in check_mount(" M39 ")
    assert "not a recognised" in check_mount("Z99")


def test_extract_listing_runs_with_tracking_disabled(monkeypatch):
    # extract_listing is wrapped in @opik.track; with OPIK_TRACK_DISABLE=true it is a plain call.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key-for-offline-test")
    stub = TestModel(call_tools=[], custom_output_args={"brand": "Kestrel", "accessories": []})
    with agent.override(model=stub):
        listing = extract_listing("Kestrel body, $95")
    assert listing["brand"] == "Kestrel" and listing["price_usd"] is None
    json.dumps(listing)
