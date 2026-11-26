"""Offline tests: no provider keys, no Opik. Run with OPIK_TRACK_DISABLE=true."""

from types import SimpleNamespace

import pypdf

from rulebook.corpus import games, pdfs
from rulebook.qa.engine import ask
from rulebook.suite.checks import citation_ok, parse_citations
from rulebook.suite.items import CASES


def test_every_rulebook_renders_to_a_readable_pdf(tmp_path):
    paths = pdfs.generate_all(tmp_path)
    assert len(paths) == 3
    text = pypdf.PdfReader(paths[0]).pages[0].extract_text()
    assert "Section 3: Scoring" in text


def test_ensure_pdfs_regenerates_missing_input(tmp_path):
    pdfs.ensure_pdfs(tmp_path)
    assert {p.name for p in tmp_path.glob("*.pdf")} == {f"{b.slug}.pdf" for b in games.RULEBOOKS}


def test_citation_parsing_handles_multiple_games():
    answer = "Draw 2. [Saltmarsh Couriers, Section 2; Lanternfall, Section 1]"
    assert parse_citations(answer) == {("Saltmarsh Couriers", "2"), ("Lanternfall", "1")}


def test_citation_check_requires_exact_game_and_section():
    assert citation_ok("Five. [Lanternfall, Section 1]", "Lanternfall", "1")
    assert not citation_ok("Five. [Quillfire Duel, Section 1]", "Lanternfall", "1")
    assert not citation_ok("Five. [Lanternfall, Section 2]", "Lanternfall", "1")


def test_unanswerable_cases_must_cite_nothing():
    assert citation_ok("The rulebook does not cover that.", "Lanternfall", "")
    assert not citation_ok("Seven. [Saltmarsh Couriers, Section 4]", "Lanternfall", "")


def test_suite_cases_point_at_real_sections():
    sections = {b.title: {s.number for s in b.sections} for b in games.RULEBOOKS}
    for case in CASES:
        assert case.game in sections
        assert case.section == "" or case.section in sections[case.game]


def test_ask_returns_answer_and_sources_from_a_stub_engine():
    node = SimpleNamespace(node=SimpleNamespace(metadata={"file_name": "x.pdf"}, text="rule"), score=0.9)
    class Resp(SimpleNamespace):
        def __str__(self): return "ruling"
    engine = SimpleNamespace(query=lambda q: Resp(source_nodes=[node]))
    out = ask(engine, "q?")
    assert out["answer"] == "ruling" and out["sources"][0]["file"] == "x.pdf"


def test_traced_handler_install_is_harmless_with_tracking_disabled():
    from rulebook import tracing

    tracing.enable_tracing()
    tracing.enable_tracing()  # idempotent
    tracing.flush()
