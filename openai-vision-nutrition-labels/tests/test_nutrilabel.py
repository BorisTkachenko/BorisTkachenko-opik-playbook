"""Offline tests: no provider keys, no Opik server (OPIK_TRACK_DISABLE=true)."""

import json
from types import SimpleNamespace

from PIL import Image

from nutrilabel import extract, render
from nutrilabel.cli import build_parser
from nutrilabel.schema import parse_facts
from nutrilabel.suite import assertions_for, build_items


def test_render_all_writes_one_png_per_product(tmp_path):
    paths = render.render_all(tmp_path)
    assert len(paths) == len(render.load_products()) == 8
    assert all(Image.open(p).size[0] > 100 for p in paths)


def test_hard_labels_differ_from_clean_ones():
    products = {p["id"]: p for p in render.load_products()}
    assert render.render_label(products["pasta-tiny"]).size[0] < 300  # shrunk
    w, h = render.render_label(products["ginger-chews-rotated"]).size
    assert w > 520  # rotation expands the canvas


def test_missing_line_is_not_drawn():
    kefir = next(p for p in render.load_products() if p["id"] == "kefir-no-sodium")
    assert "Sodium" not in [left for left, _, _ in render.label_lines(kefir)]


def test_parse_facts_normalises_types_and_allergens():
    facts = parse_facts(json.dumps({
        "product_name": "X", "serving_size": "1 cup", "calories": "170", "sodium_mg": None,
        "protein_g": 4, "total_fat_g": 1.5, "allergens": ["Milk ", "SOY", "milk"],
    }))
    assert facts.calories is None  # a string is not a number
    assert facts.protein_g == 4.0 and facts.sodium_mg is None
    assert facts.allergens == ["milk", "soy"]


def test_assertions_carry_expected_values_and_null_sodium():
    items = {i["data"]["image"].split("/")[-1]: i for i in build_items()}
    assert any("sodium_mg is null" in a for a in items["kefir-no-sodium.png"]["assertions"])
    peanut = " ".join(assertions_for(next(p for p in render.load_products() if p["id"] == "peanut-bar")))
    assert "peanuts, soy, milk" in peanut and "calories is 230" in peanut


def test_traced_extract_runs_with_tracking_disabled(tmp_path, monkeypatch):
    """@opik.track is a pass-through here: the stubbed model reply comes straight back."""
    image = tmp_path / "x.png"
    Image.new("RGB", (10, 10)).save(image)
    reply = json.dumps({"product_name": "Stub", "calories": 99, "allergens": []})
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))]))))
    monkeypatch.setattr(extract, "_client", fake)
    out = extract.extract_label(str(image))
    assert out["product_name"] == "Stub" and out["calories"] == 99.0


def test_cli_has_three_subcommands():
    parser = build_parser()
    for cmd in ("render", "extract", "suite"):
        assert parser.parse_args([cmd]).command == cmd
