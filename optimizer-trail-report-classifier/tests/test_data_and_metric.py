from trailclass.config import LABELS
from trailclass.data import load_split
from trailclass.metric import CategoryMatch, is_correct, normalize, trail_report_accuracy


def test_splits_are_labelled_and_disjoint():
    train, validation = load_split("train"), load_split("validation")
    assert len(train) == 24 and len(validation) == 18
    assert {r["label"] for r in train + validation} == set(LABELS)
    assert not {r["report"] for r in train} & {r["report"] for r in validation}


def test_normalize_accepts_formatting_variants_only():
    assert normalize("Trail hazard.") == "trail_hazard"
    assert normalize("`wildlife-sighting`") == "wildlife_sighting"
    assert not is_correct("This is a trail_hazard report", "trail_hazard")


def test_metric_functions_agree():
    item = {"label": "compliment"}
    assert trail_report_accuracy(item, "Compliment") == 1.0
    assert trail_report_accuracy(item, "other") == 0.0
    assert CategoryMatch().score(output="compliment", label="compliment").value == 1.0
