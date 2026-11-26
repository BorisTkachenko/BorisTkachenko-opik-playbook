# ollama-homebrew-rag

*A home-brewing assistant that runs entirely on your laptop, and still gives you a full trace of every answer.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat) ![Ollama](https://img.shields.io/badge/ollama-llama3.2%3A1b-grey?style=flat) [![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)](https://github.com/comet-ml/opik)

Small local models are the ones that most need observability. A 1B-parameter model will happily ignore the context you hand it, and when an answer is wrong you want to know whether retrieval fetched the wrong passage or the model fumbled the right one. This example is a complete RAG pipeline with zero cloud LLM calls: embeddings and chat both come from a local Ollama, the index is a JSON file on disk, and Opik receives one trace per question with retrieval as its own span.

## What you'll build

A small Python package, `homebrew_rag`, over a fictional home-brewing guide in `docs/` (mashing, hop schedules, fermentation temperatures, off-flavour troubleshooting). It is split by stage, with a CLI on top:

- `ingest/` splits each guide at its `##` headings and embeds the 13 chunks with `nomic-embed-text`.
- `retrieve/` loads the index and does cosine search with numpy.
- `answer/` builds a LangChain prompt | `ChatOllama` (`llama3.2:1b`) | parser chain and runs one question end to end.
- `cli.py` offers `ingest`, `ask "..."`, and `demo` (ingest, then three scripted questions).

## See it in Opik

Open the **ollama-homebrew-rag** project and the **Traces** tab. One `demo` run gives you four traces: one `ingest_docs` and three `ask_brewing_guide`. Click an `ask_brewing_guide` trace and expand the tree. You will see six spans:

- `ask_brewing_guide` (general), the root, with your question in and the answer plus source sections out.
- `search_guide` (tool), the retrieval step. Its output is the two best chunks with their file, heading and cosine score. For "My beer tastes like butterscotch" the top hit is `troubleshooting.md` "Buttery or butterscotch taste", and the second one is the off-topic "Green apple taste" section, which is exactly the kind of thing you spot here and not in the answer.
- `answer_from_excerpts` (general) with three children: `ChatPromptTemplate` (tool), `ChatOllama` (llm) and `StrOutputParser` (general). The `ChatOllama` span holds the fully assembled prompt and the raw generation.

Two honest limits. Ollama through LangChain reports no token usage to Opik, so the Usage and Estimated cost columns are empty: the lesson here is tracing, not cost. And the model name is not in the span's Model field; look in the span's metadata, where `ls_model_name` is `llama3.2:1b` and `ls_provider` is `ollama`.

## Run it yourself

1. Install Ollama natively (macOS: `brew install ollama`, or the installer from ollama.com) and start it (`ollama serve`, or open the app).
2. Pull the two models (about 1.6 GB together):
   ```
   ollama pull llama3.2:1b
   ollama pull nomic-embed-text
   ```
3. Have an Opik to send traces to. For self-hosted Opik put `OPIK_URL_OVERRIDE` (and `OPIK_WORKSPACE`) in a `.env` in this folder or any parent; see `.env.example`. Opik Cloud users add `OPIK_API_KEY` instead.
4. From this folder:
   ```
   uv sync
   uv run homebrew-rag demo
   ```
   The `demo` run took about 30 seconds on a laptop with the models already pulled. Ask your own question with `uv run homebrew-rag ask "How long should I dry hop?"` (run `ingest` once first).

`OLLAMA_BASE_URL` overrides the default `http://localhost:11434`.

## Poke around

- Ask something the guide does not cover ("How do I brew mead?") and compare the `search_guide` scores with a covered question; the model should say the excerpts do not cover it, though a 1B model sometimes will not.
- Change `TOP_K` in `homebrew_rag/config.py` to 1 or 4 and watch the `ChatOllama` prompt grow or shrink.
- Swap `EMBED_MODEL` for another embedding model, re-run `ingest`, and see how the scores move.
- Unplug the network: everything still works except delivery of traces to a cloud Opik.

## Gotchas we hit

**Warning: "You are attempting to log data into a nested span under the project name ... However, the project name 'Default Project' from parent span will be used instead."**
Cause: `OpikTracer(project_name=...)` ran inside an `@opik.track` function that had no project of its own, so the parent span resolved to the default project. Fix: give every decorator the project, `@opik.track(name="ask_brewing_guide", project_name=config.PROJECT_NAME)`, and pass the same name to `OpikTracer`.

**The Model, Usage and Cost columns are empty on the `ChatOllama` span.**
Cause: `langchain-ollama` 1.2 with Opik 2.3.4 logs no `usage`, and the model name only lands in metadata (`ls_model_name`). Nothing to fix; read the model from metadata and do not expect cost for local models.

**Retrieval would be invisible if it were a LangChain retriever.**
`OpikTracer` has been seen to drop retriever runs, so retrieval here is a plain function decorated `@opik.track(name="search_guide", type="tool")`; it always appears as its own span, nested under the question's trace because the tracer runs inside the same tracked call. (We use the decorator rather than a retriever by design and did not test the retriever variant.)

## How it's put together

- `homebrew_rag/config.py`: loads `.env`, sets the Opik project, model names and paths.
- `homebrew_rag/ingest/chunker.py`, `indexer.py`: section chunking; embedding plus the traced `ingest_docs`.
- `homebrew_rag/retrieve/store.py`, `search.py`: cosine index; traced `search_guide`.
- `homebrew_rag/answer/chain.py`, `ask.py`: prompt and chat model; the traced `ask_brewing_guide` with `OpikTracer`.
- `homebrew_rag/cli.py`: `ingest`, `ask`, `demo`; flushes Opik at the end.
- `docs/`: the four fictional guides. `tests/test_rag.py`: offline tests for chunking, cosine ranking, prompt formatting, and a traced function with tracking disabled.

Run the tests with `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
