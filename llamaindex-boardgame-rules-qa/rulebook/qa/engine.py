"""The rules-lawyer query engine: retrieve rule chunks, then synthesize a cited ruling."""

from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine

RULING_PROMPT = PromptTemplate(
    "You are a strict rules lawyer for a shelf of board games. Use ONLY the rulebook "
    "excerpts below. Quote exact numbers. End every ruling with a citation in the form "
    "[Game, Section N] for each rule you relied on. If the excerpts do not settle the "
    "question, say the rulebooks do not cover it.\n"
    "---------------------\n{context_str}\n---------------------\n"
    "Question: {query_str}\nRuling: "
)


def make_engine(index: VectorStoreIndex, top_k: int = 4) -> BaseQueryEngine:
    return index.as_query_engine(similarity_top_k=top_k, text_qa_template=RULING_PROMPT)


def ask(engine: BaseQueryEngine, question: str) -> dict:
    """Run one question; return the answer plus the chunks retrieval supplied."""
    response = engine.query(question)
    return {
        "answer": str(response),
        "sources": [
            {"file": n.node.metadata.get("file_name"), "score": n.score, "text": n.node.text}
            for n in response.source_nodes
        ],
    }
