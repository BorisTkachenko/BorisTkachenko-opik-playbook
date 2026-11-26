"""Turn the rulebook PDFs into a persisted LlamaIndex vector index."""

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from rulebook.config import EMBED_MODEL, LLM_MODEL, PDF_DIR, STORAGE_DIR
from rulebook.corpus.pdfs import ensure_pdfs


def configure_models() -> None:
    Settings.llm = OpenAI(model=LLM_MODEL, temperature=0.0)
    Settings.embed_model = OpenAIEmbedding(model=EMBED_MODEL)
    # Small chunks keep neighbouring sections of a rulebook from blending into one.
    Settings.node_parser = SentenceSplitter(chunk_size=200, chunk_overlap=20)


def build_index() -> VectorStoreIndex:
    configure_models()
    ensure_pdfs()
    documents = SimpleDirectoryReader(str(PDF_DIR), required_exts=[".pdf"], exclude_hidden=False).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=str(STORAGE_DIR))
    return index


def load_index() -> VectorStoreIndex:
    configure_models()
    if not STORAGE_DIR.exists():
        return build_index()
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(STORAGE_DIR)))
