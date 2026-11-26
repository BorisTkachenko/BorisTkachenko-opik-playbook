"""One question end to end: retrieve, then answer."""

import opik
from opik.integrations.langchain import OpikTracer

from .. import config
from ..retrieve import Index, search_guide
from .chain import build_chain, format_context


# The outer decorator makes the whole question one trace ("ask_brewing_guide");
# search_guide and the chain below become its child spans.
@opik.track(
    name="ask_brewing_guide", tags=["ollama", "rag", "local"], project_name=config.PROJECT_NAME
)
def ask(question: str, index: Index) -> dict:
    hits = search_guide(question, index)
    # OpikTracer logs the chain as nested spans (prompt, a ChatOllama llm span whose
    # metadata carries ls_model_name=llama3.2:1b). It runs inside the tracked function, so it attaches
    # to this trace rather than starting a second one. Ollama reports no token
    # usage through LangChain, so these spans carry no usage or cost.
    tracer = OpikTracer(project_name=config.PROJECT_NAME)
    answer = build_chain().invoke(
        {"context": format_context(hits), "question": question},
        config={"callbacks": [tracer], "run_name": "answer_from_excerpts"},
    )
    return {"answer": answer, "sources": [f'{h["source"]}#{h["heading"]}' for h in hits]}
