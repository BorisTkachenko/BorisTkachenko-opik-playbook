"""The retrieval step, wrapped so it shows up as its own span."""

import opik
from langchain_ollama import OllamaEmbeddings

from .. import config
from .store import Index


# OpikTracer can drop LangChain retriever runs, so retrieval is not a LangChain
# retriever at all: this named tool span carries the question in and the
# retrieved sections (with scores) out, and nests under the trace of whoever calls it.
@opik.track(name="search_guide", type="tool", project_name=config.PROJECT_NAME)
def search_guide(question: str, index: Index, k: int = config.TOP_K) -> list[dict]:
    vector = OllamaEmbeddings(
        model=config.EMBED_MODEL, base_url=config.OLLAMA_BASE_URL
    ).embed_query(question)
    return index.top_k(vector, k)
