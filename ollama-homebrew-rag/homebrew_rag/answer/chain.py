"""Prompt + local chat model."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from .. import config

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a home-brewing assistant. Answer using only the guide excerpts "
     "below. If they do not cover the question, say so. Use at most three sentences.\n\n"
     "{context}"),
    ("human", "{question}"),
])


def format_context(hits: list[dict]) -> str:
    return "\n\n---\n\n".join(h["text"] for h in hits)


def build_chain():
    llm = ChatOllama(
        model=config.CHAT_MODEL, base_url=config.OLLAMA_BASE_URL,
        temperature=0, num_predict=200,
    )
    return PROMPT | llm | StrOutputParser()
