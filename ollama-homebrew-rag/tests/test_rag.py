import numpy as np

from homebrew_rag.answer import chain, format_context
from homebrew_rag.ingest import chunk_markdown
from homebrew_rag.retrieve import Index, cosine_top_k, search_guide
from homebrew_rag import config


def test_chunker_one_chunk_per_section():
    chunks = chunk_markdown(config.DOCS_DIR / "mashing.md")
    assert len(chunks) == 3
    assert chunks[0]["heading"] == "Strike water and mash temperature"
    assert chunks[0]["text"].startswith("Mashing Guide / Strike water")


def test_cosine_top_k_orders_by_similarity():
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])
    assert [i for i, _ in cosine_top_k([1.0, 0.0], matrix, 2)] == [0, 2]


def test_prompt_and_context_formatting():
    ctx = format_context([{"text": "A"}, {"text": "B"}])
    msgs = chain.PROMPT.format_messages(context=ctx, question="Q?")
    assert "A\n\n---\n\nB" in msgs[0].content and msgs[1].content == "Q?"


def test_traced_search_runs_with_tracking_disabled(monkeypatch):
    # search_guide is an @opik.track function; with OPIK_TRACK_DISABLE=true it is a plain call.
    class FakeEmb:
        def __init__(self, **_): pass
        def embed_query(self, _): return [0.0, 1.0]
    monkeypatch.setattr("homebrew_rag.retrieve.search.OllamaEmbeddings", FakeEmb)
    index = Index([
        {"source": "a.md", "heading": "x", "text": "x", "vector": [1.0, 0.0]},
        {"source": "b.md", "heading": "y", "text": "y", "vector": [0.0, 1.0]},
    ])
    hits = search_guide("q", index, k=1)
    assert hits[0]["source"] == "b.md" and hits[0]["score"] == 1.0
