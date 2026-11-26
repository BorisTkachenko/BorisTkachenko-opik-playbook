"""Opik tracing for LlamaIndex: one callback handler, installed once per process."""

import opik
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from opik.integrations.llama_index import LlamaIndexCallbackHandler

from rulebook.config import PROJECT_NAME

_installed = False


def enable_tracing() -> None:
    """Route every LlamaIndex event to Opik, under this example's own project."""
    global _installed
    if _installed:
        return
    # The handler turns each query into one trace: retrieve (with its embedding call) and
    # synthesize (chunking, templating, llm) become child spans. Passing project_name
    # keeps traces out of "Default Project"; skipping index construction keeps `build`
    # from logging one giant embedding trace per run.
    handler = LlamaIndexCallbackHandler(project_name=PROJECT_NAME, skip_index_construction_trace=True)
    Settings.callback_manager = CallbackManager([handler])
    _installed = True


def flush() -> None:
    # Traces are shipped from a background thread; without a flush a short CLI run can
    # exit before the last trace is sent and it never appears in Opik.
    opik.flush_tracker()
