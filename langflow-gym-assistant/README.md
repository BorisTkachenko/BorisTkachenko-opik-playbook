<div align="center">

# 🏋️ Gym front desk in Langflow

**`langflow-gym-assistant`**

*A drag-and-drop chatbot whose every answer can be checked in Opik, using the tracer already built into Langflow.*

[![Langflow](https://img.shields.io/badge/Langflow-1.13.4-7528fc?style=flat)](https://www.langflow.org)
[![model](https://img.shields.io/badge/model-gpt--4o--mini-10a37f?style=flat)](https://platform.openai.com/docs/models/gpt-4o-mini)
[![runs in](https://img.shields.io/badge/runs%20in-docker-2496ed?style=flat)](https://docs.docker.com/compose/)

</div>

---

Ironwood Community Gym is made up, and so are its prices, but its problem is real. The front desk answers the same questions all day: what does Plus cost, can I freeze my membership, when is yoga. Someone wired up a chatbot in Langflow in an afternoon. It reads the gym's fact sheet, remembers the conversation, and answers in two or three sentences.

A chatbot like that will get some answers wrong. Here, one prospective member asks for the cheapest way to do yoga twice a week and is told **45 dollars a month**. That's the Basic plan plus *two* classes, not two a week, and Plus at 49 dollars is clearly the better deal. Nobody will notice that from the canvas. This example uses Langflow's built-in Opik tracer so every turn of every conversation lands in Opik, grouped by conversation, where mistakes like this are easy to find.

## What you'll build

A Langflow container with one flow, **Gym front desk**, built headlessly from Langflow's own *Memory Chatbot* starter:

**Chat Input** → **Message History** → **Prompt Template** (gym facts + rules) → **Language Model** (gpt-4o-mini) → **Chat Output**

`setup.py` patches the starter: it writes the facts from `data/gym-facts.md` into the prompt, selects gpt-4o-mini, and points the API Key field at Langflow's `OPENAI_API_KEY` global variable, so the key is never stored in the flow. `demo.py` then plays three scripted members (`data/conversations.json`) through Langflow's `/api/v1/run` endpoint, each with its own `session_id`.

Opik is switched on by environment variables only, in `docker-compose.yml`:

- `OPIK_URL_OVERRIDE`: where Opik is. `setup.sh` rewrites `localhost` to `host.docker.internal` so the container can reach an Opik on your machine.
- `OPIK_WORKSPACE`, plus `OPIK_API_KEY` for Opik Cloud only.
- `LANGCHAIN_PROJECT=langflow-gym-assistant`: Langflow's tracers take the project name from this variable. Without it, everything lands in a project called "Langflow".

## See it in Opik

Open the **`langflow-gym-assistant`** project. After one demo run it holds **6 traces**, one per member message. Each trace is named after the flow's id, and the **Threads** tab groups them into **3 threads**, one per `session_id`: `dana-joining` (3 turns), `marco-freeze` (2) and `lena-sauna` (1). Open the `dana-joining` thread and it reads as the conversation she had.

Inside a trace there is one span per component that ran, in flow order: **`Chat Input`**, **`Message History`**, **`Type Convert`**, **`Prompt Template`**, **`Language Model`** and **`Chat Output`**. Inside the Language Model's work are the two spans LangChain adds:

- **`ChatPromptTemplate`**: the prompt with the facts and the conversation so far filled in.
- **`ChatOpenAI`** (llm): the exact messages sent to gpt-4o-mini and its reply, with token usage and an estimated cost.

The six calls together cost about **$0.001**. Open `Message History` on Dana's later turns to see her earlier messages being read back. That's also why her prompts grow: 593, then 1,317, then 1,872 prompt tokens over her three turns.

Now open Dana's first turn and expand `ChatOpenAI`. The input contains the price list (*"Basic: 29 dollars per month … Classes cost 8 dollars each"*, *"Plus: 49 dollars per month … unlimited group classes"*) and the output says *"totaling 45 dollars for the month"*. The facts were right there and the arithmetic was not. That's a prompt problem (nothing asks the model to work out a monthly total), and the trace shows it in one click. Lena's sauna question shows the opposite: the facts don't mention a sauna, and the model says it doesn't know instead of inventing one.

## Run it yourself

You need Docker, `python3`, an OpenAI key and an Opik. For a self-hosted Opik on the same machine, see the [local deployment guide](https://www.comet.com/docs/opik/self-host/local_deployment).

1. Put `OPENAI_API_KEY`, `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` in the repo-root `.env` (see `.env.example` in this folder). Add `OPIK_API_KEY` for Opik Cloud.
2. `./setup.sh` starts Langflow on `localhost:7860` and creates the flow.
3. `./demo.sh` plays the three conversations and prints every answer.
4. Optional: `uv run --with opik python check_opik.py` prints the same summary as above, read back from Opik.

To stop: `docker compose down` (`-v` also deletes the flows and chat history).

## Poke around

- **Fix the yoga answer.** Open `localhost:7860`, add "when asked for the cheapest option, compare monthly totals for the stated frequency" to the Prompt Template, and rerun `./demo.sh`. Then compare Dana's two first-turn traces in Opik.
- **Break the memory.** Set Message History's `n_messages` to 1 and rerun. Marco's "how do I cancel then?" loses its context, and the shrinking prompt in the `ChatOpenAI` span shows why.
- **Ask something off the sheet.** Send "Do you have parking?" with a new `session_id` and check whether the answer stays inside the facts.

## Gotchas we hit

**Traces arrive with only `Language Model`, `ChatPromptTemplate` and `ChatOpenAI`; the other components are missing.** The Langflow container log shows `TypeError: Opik.span() got an unexpected keyword argument 'source'` once per component. Cause: Langflow 1.13.4's tracer finishes each component span with `self._client.span(**span.__dict__)`, and the span object carries fields that `Opik.span()` doesn't accept: `source` in every opik 2.x release, and also `environment` from 2.1. Pinning another opik 2.x won't help. Fix: this example builds a one-line patch into the image (`Dockerfile` + `patch_opik_tracer.py`) that passes only the keyword arguments `Opik.span()` accepts. The patch refuses to build if the line ever changes, so a Langflow upgrade won't silently skip it.

**`Model name/provider overrides require a built-in model selection, not a connected model object.`** You get this when you fill only the Language Model's *Model Name Override* (and *Provider Override*) through the API. Cause: the component's `model` field must hold a full model-selection object from Langflow's catalogue, and the overrides only patch that object. Fix: `setup.py` takes an OpenAI entry from `GET /api/v1/model_options/language`, renames it to `gpt-4o-mini`, and clears its `reasoning` flags. The catalogue's default OpenAI entries are reasoning models, and gpt-4o-mini would get reasoning parameters it doesn't accept.

**`HTTP Error 403: Forbidden` from `/api/v1/run/{flow_id}`,** even with a valid login token. Cause: in Langflow 1.13 the run endpoint only accepts a Langflow API key. Fix: `demo.py` mints one with `POST /api/v1/api_key/` and sends it as `x-api-key`.

## How it's put together

- `Dockerfile` / `patch_opik_tracer.py`: `langflowai/langflow:1.13.4` plus the tracer fix above.
- `docker-compose.yml`: builds that image and runs it with auto-login, `OPENAI_API_KEY` exposed as a Langflow global variable, and the Opik variables for the built-in tracer.
- `setup.sh`: works out the Opik URL as the container sees it, starts Langflow, and runs `setup.py`.
- `setup.py`: builds the flow from the Memory Chatbot starter over Langflow's REST API (standard library only).
- `demo.sh` / `demo.py`: play `data/conversations.json` through `/api/v1/run`, one `session_id` per member.
- `check_opik.py`: reads the traces back from Opik and summarises threads, spans and cost.
- `data/gym-facts.md`: the fictional gym's plans, hours, class schedule and rules.

---

<sub>built with [Opik](https://github.com/comet-ml/opik) · inspired by Opik's examples and documentation</sub>
