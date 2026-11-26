"""Embed every chunk with a local model and write the index to disk."""

import json
import pathlib

import opik
from langchain_ollama import OllamaEmbeddings

from .. import config
from .chunker import chunk_markdown


def embed_texts(texts: list[str]) -> list[list[float]]:
    return OllamaEmbeddings(
        model=config.EMBED_MODEL, base_url=config.OLLAMA_BASE_URL
    ).embed_documents(texts)


# type="tool" makes indexing one trace with a single span: input is the folder,
# output the chunk count. Embedding calls are plain HTTP to Ollama, so LangChain
# callbacks never see them; this decorator is what makes ingest visible at all.
@opik.track(name="ingest_docs", type="tool", project_name=config.PROJECT_NAME)
def build_index(docs_dir: pathlib.Path, index_path: pathlib.Path) -> dict:
    chunks = [c for p in sorted(docs_dir.glob("*.md")) for c in chunk_markdown(p)]
    vectors = embed_texts([c["text"] for c in chunks])
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(
        {"embed_model": config.EMBED_MODEL,
         "chunks": [{**c, "vector": v} for c, v in zip(chunks, vectors)]}
    ))
    return {"chunks": len(chunks), "dimensions": len(vectors[0]), "index": index_path.name}
