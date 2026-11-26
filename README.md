<div align="center">

# 📒 Opik Playbook

**22 small, complete LLM apps, each one built to show a single thing you can see, measure or fix with [Opik](https://github.com/comet-ml/opik).**

[![examples](https://img.shields.io/badge/examples-22-4f46e5?style=flat)](#the-plays)
[![Python](https://img.shields.io/badge/Python-11-3776ab?style=flat&logo=python&logoColor=white)](#the-plays)
[![TypeScript](https://img.shields.io/badge/TypeScript-8-3178c6?style=flat&logo=typescript&logoColor=white)](#the-plays)
[![Java](https://img.shields.io/badge/Java-1-b07219?style=flat)](#the-plays)
[![low-code](https://img.shields.io/badge/low--code-2-ea4b71?style=flat)](#the-plays)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat)](LICENSE)

</div>

---

A playbook is a set of moves you can run when a situation comes up. Each folder here is one move. The cases are things like "my agent handed off to the wrong specialist", "this prompt got worse and I can't tell why", "the low-code workflow nobody instrumented just turned a volunteer away", and "the JVM service's LLM calls show up with no content". Every example is a small app with fictional data, a real model call or two, and a README that says exactly which trace, span, thread or experiment to open in Opik and what you'll find there.

The numbers in each README come from an actual run, honest failures included. Several test suites deliberately don't pass 100%, and the READMEs explain why.

## The plays

### 🔍 See what an agent actually did

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`openai-agents-insurance-claims`](openai-agents-insurance-claims) | OpenAI Agents SDK | Py | Triage → specialist **handoffs** and tool calls as one span tree; each claim conversation as a **thread** |
| [`mastra-banking-agent`](mastra-banking-agent) | Mastra · OTLP | TS | Agent-loop trees with real `execute_tool` spans for balance, transactions and card freezes |
| [`beeai-cfp-triage-agent`](beeai-cfp-triage-agent) | BeeAI · OpenInference | TS | Every ReAct **iteration** with its llm and tool spans, for a conference talk-proposal triage |
| [`smolagents-weather-station-analyst`](smolagents-weather-station-analyst) | smolagents · OpenInference | Py | The **pandas code** a CodeAgent wrote and its execution logs, step by step |
| [`crewai-wedding-planner`](crewai-wedding-planner) | CrewAI | Py | One trace per crew kickoff and the **token and dollar split per agent** |
| [`temporal-podcast-publishing`](temporal-podcast-publishing) | Temporal · OpenAI | TS | One trace across **two OS processes**, with a failed upload attempt and its retry |

### 💬 Follow a conversation

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`langchainjs-fastify-bike-shop-chat`](langchainjs-fastify-bike-shop-chat) | LangChain.js · Fastify | TS | **Threads** that read as clean transcripts, because each turn's root is plain text in and out |
| [`vercel-ai-sveltekit-garden-chat`](vercel-ai-sveltekit-garden-chat) | Vercel AI SDK · SvelteKit | TS | **Streaming** replies as complete spans, threads, and a live **online-evaluation rule** scoring every turn |
| [`langflow-gym-assistant`](langflow-gym-assistant) | Langflow (Docker) | low-code | Langflow's **built-in tracer**: a span per component, one thread per member session |

### ✅ Test it, measure it, catch it

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`anthropic-ts-museum-guide-citations`](anthropic-ts-museum-guide-citations) | Anthropic SDK | TS | A **test suite** with plain-English assertions that every quote is verbatim from the placards |
| [`pydantic-ai-camera-listing-extraction`](pydantic-ai-camera-listing-extraction) | Pydantic AI · OTel | Py | A suite that catches **invented field values** in typed extraction (honest 1/6) |
| [`llamaindex-boardgame-rules-qa`](llamaindex-boardgame-rules-qa) | LlamaIndex | Py | Retrieve/synthesize spans over generated rulebook PDFs and a **rule-level suite** |
| [`openai-vision-nutrition-labels`](openai-vision-nutrition-labels) | OpenAI vision | Py | Label **images attached** to every trace, and a suite that fails on the smudged one |
| [`whisper-vet-voicemail-triage`](whisper-vet-voicemail-triage) | OpenAI TTS + Whisper | Py | A **playable MP3** on each trace, and judge flakiness tamed with an execution policy |
| [`litellm-flashcard-router`](litellm-flashcard-router) | LiteLLM | Py | The same workload on two providers, compared by **cost and latency** |

### 🧪 Improve the prompt, prove it improved

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`prompt-library-ts-release-notes`](prompt-library-ts-release-notes) | Opik TS SDK | TS | **Prompt versions** v1 → v2 with a diff; one suite scores them 0/5 and 5/5 |
| [`dspy-astronomy-fact-checker`](dspy-astronomy-fact-checker) | DSPy | Py | **Uncompiled vs compiled** experiments on the same claims: 0/12 → 12/12 |
| [`optimizer-trail-report-classifier`](optimizer-trail-report-classifier) | Opik Agent Optimizer | Py | An **optimization run's score curve**, a held-out check, and the winner saved to the prompt library |

### 🔌 Bring traces in from anywhere

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`quarkus-langchain4j-pharmacy-faq`](quarkus-langchain4j-pharmacy-faq) | Quarkus · LangChain4j · OTLP | Java | **JVM** spans over OTLP, with prompt and completion content on the llm span |
| [`voltagent-restaurant-reservations`](voltagent-restaurant-reservations) | VoltAgent · OTLP | TS | The **`gen_ai.*` attribute mapping** that turns blank spans into priced llm spans |
| [`ollama-homebrew-rag`](ollama-homebrew-rag) | LangChain · Ollama | Py | Full RAG traces with **zero cloud LLM calls** |
| [`n8n-food-bank-volunteers`](n8n-food-bank-volunteers) | n8n (Docker) | low-code | **Zero-code** tracing via hooks: every workflow run, every node, the IF branch taken |

## Running a play

Every folder stands on its own. The general shape:

1. **Have an Opik.** Self-host it locally ([guide](https://www.comet.com/docs/opik/self-host/local_deployment), UI on `http://localhost:5173`) or use Opik Cloud.
2. **Set your keys once.** Copy [`.env.example`](.env.example) to `.env` at the repo root and fill in what you need. Every example walks up to that file, so there's one place to keep credentials. It's git-ignored.
3. **Open the folder and follow its README.** It's usually one of:
   - Python: `uv sync && uv run main.py` (or the CLI the README names)
   - TypeScript: `npm install && npm run demo`
   - Java: `./run.sh`
   - Docker / low-code: `./setup.sh && ./demo.sh`
4. **Open the project named after the folder in Opik.** Each README's *See it in Opik* section says where to click.

Every example ships offline tests that need no provider keys and no Opik:

```bash
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest   # Python
npm test                                                                            # TypeScript (each README names its switch)
mvn test                                                                            # Java
python3 -m unittest discover -s tests -v                                            # n8n / Langflow
```

## What's in a folder

- **`README.md`**: the problem, what you'll build, *See it in Opik* (with the numbers from a real run), exact run steps, a few experiments to try, and a **Gotchas** section of things that actually went wrong while building it, with the fix.
- **The app**: small enough to read in one sitting, with a short comment at every Opik touchpoint saying what it produces in the UI.
- **`data/` or `docs/`**: fictional inputs (no external APIs, no real datasets). Generated media is produced at run time.
- **`.env.example`**: only the variables that example reads.
- **`tests/`** (`src/test` for Java): a handful of offline tests. In the Python and TypeScript examples, one of them calls a traced function with tracking off.
- **Git history**: each example arrived as a short series of commits, often a plain app first and then the commit that adds Opik. `git log -- <folder>` shows the diff from "works" to "observable".

## License

[Apache 2.0](LICENSE).

---

<sub>inspired by [Opik](https://github.com/comet-ml/opik)'s examples and [documentation](https://www.comet.com/docs/opik/)</sub>
