from trailclass.config import LABELS
from trailclass.data import load_split
from trailclass.metric import CategoryMatch, is_correct, normalize, trail_report_accuracy


def test_splits_are_labelled_and_disjoint():
    train, validation = load_split("train"), load_split("validation")
    assert len(train) == 49 and len(validation) == 32
    assert {r["label"] for r in train + validation} == set(LABELS)
    assert not {r["report"] for r in train} & {r["report"] for r in validation}


def test_extract_label_reads_schema_json_and_loose_text():
    from trailclass.metric import extract_label

    assert extract_label('{"category": "lost_and_found"}') == "lost_and_found"
    assert extract_label("Lost and found") == "lost_and_found"
    assert extract_label("I would call this a wildlife sighting.") == "wildlife_sighting"
    assert extract_label("trail hazard or facility issue") == ""


def test_normalize_accepts_formatting_variants_only():
    assert normalize("Trail hazard.") == "trail_hazard"
    assert normalize("`wildlife-sighting`") == "wildlife_sighting"
    assert normalize("This is a trail_hazard report") != "trail_hazard"


def test_metric_functions_agree():
    item = {"label": "compliment"}
    item["report"] = "Thank you!"
    assert trail_report_accuracy(item, "Compliment").value == 1.0
    wrong = trail_report_accuracy(item, "other")
    assert wrong.value == 0.0 and "expected compliment" in wrong.reason
    assert CategoryMatch().score(output="compliment", label="compliment").value == 1.0
