<div align="center">

# 🥫 Volunteer screening in n8n

**`n8n-food-bank-volunteers`**

*A no-code sign-up workflow where every run shows up in Opik, and nobody wrote tracing code.*

[![n8n](https://img.shields.io/badge/n8n-2.41.7-ea4b71?style=flat)](https://n8n.io)
[![n8n-observability](https://img.shields.io/badge/n8n--observability-1.0.3-6b7280?style=flat)](https://www.npmjs.com/package/n8n-observability)
[![model](https://img.shields.io/badge/model-gpt--4o--mini-10a37f?style=flat)](https://platform.openai.com/docs/models/gpt-4o-mini)
[![runs in](https://img.shields.io/badge/runs%20in-docker-2496ed?style=flat)](https://docs.docker.com/compose/)

</div>

---

The Riverside Community Pantry is a made-up food bank with a common problem: its volunteer sign-up form gets more submissions than the one part-time coordinator can read. Someone built an n8n workflow over a weekend. The form posts to a webhook, gpt-4o-mini checks the sign-up against the pantry's role rules (minimum ages, a driver's licence, a background check for the kids' program, shift times), and the workflow either drafts a welcome or flags the sign-up for the coordinator.

That works until someone asks why a volunteer was turned away. The workflow lives on a canvas, the prompt lives in a node, and nobody kept the model's answers. This example adds observability to that workflow without touching it. A hooks package loaded into n8n exports every execution to Opik over OpenTelemetry, so each sign-up becomes a trace with the applicant's form, the model's verdict and the branch the workflow took.

## What you'll build

A self-hosted n8n with one six-node workflow:

**Sign-up form** (webhook) → **Screen volunteer (gpt-4o-mini)** → **Approved?** (IF) → **Welcome note** *or* **Coordinator follow-up** (Set) → **Reply to form**

The model returns JSON with `decision` (`approve`, `follow_up`, `not_a_fit`), `role`, `shift`, a one-sentence `reason` and an optional `follow_up_question`. The IF node routes approvals one way and everything else to the coordinator. The webhook reply carries the result back to the form.

The tracing comes entirely from the container image. The `Dockerfile` installs [`n8n-observability`](https://www.npmjs.com/package/n8n-observability) and points n8n's `EXTERNAL_HOOK_FILES` at it. `docker-compose.yml` hands it Opik's OTLP endpoint plus two headers: `Comet-Workspace` and `projectName=n8n-food-bank-volunteers`. The workflow JSON has no tracing node in it at all.

## See it in Opik

Open the **`n8n-food-bank-volunteers`** project. One run of `./demo.sh` posts four sign-ups and leaves **four traces**, all named `Volunteer screening` after the workflow.

Open any of them. The tree has the workflow execution as the root and one span per node that actually ran: `Sign-up form`, `Screen volunteer (gpt-4o-mini)`, `Approved?`, then **either** `Welcome note` **or** `Coordinator follow-up`, then `Reply to form`. So the branch is visible in the trace itself. In our run one trace went through `Welcome note` (Rosa, approved for the distribution desk on Saturday mornings) and three through `Coordinator follow-up`.

Click `Screen volunteer (gpt-4o-mini)` and open its **Input** panel. The node's full parameters are there, including the system prompt with the role rules. Two attributes matter most:

- `n8n.node.input`: the webhook payload the node received, i.e. the applicant's form.
- `n8n.node.output`: the model's parsed JSON verdict.

That pair answers the "why was this volunteer turned away" question. In our run, Owen Park (19, asked to be a delivery driver, available Tuesday and Thursday evenings) came back `not_a_fit` with the reason *"Owen is 19, which does not meet the minimum age requirement of 21 for the delivery driver role."* Reading the rules in the same span shows the model only judged the role Owen asked for. At 19 he qualifies for warehouse sorting or the distribution desk on exactly those evenings. That is a prompt bug, and it was found from a trace, not from a complaint. Priya Raman came back `follow_up` with the question *"Are you willing to complete a background check for the kids snack program?"*, which is right: her form never mentioned one.

What you will **not** see: token counts, a model column or a dollar cost. Every span is a `general` span, and at these versions the hooks attach no `gen_ai.*` usage attributes to the OpenAI node's span. The **Output** column of the trace list is also empty, because the content is stored as span attributes and shows up in the Input panel. This example is about seeing what a no-code workflow did, not what it cost.

## Run it yourself

You need Docker, `curl`, `python3`, an OpenAI key and an Opik to send to. For a self-hosted Opik on the same machine, see the [local deployment guide](https://www.comet.com/docs/opik/self-host/local_deployment).

1. Put your keys in the repo-root `.env` (copy `.env.example` from this folder): `OPENAI_API_KEY`, plus `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE`. Add `OPIK_API_KEY` only for Opik Cloud.
2. `./setup.sh` builds the image, starts n8n on `localhost:5678`, creates the owner account and the OpenAI credential, then imports and activates the workflow. It needs no browser.
3. `./demo.sh` posts the four sign-ups in `data/applicants.json` and prints each screening result.
4. Open the `n8n-food-bank-volunteers` project in Opik.

To stop: `docker compose down`. Add `-v` to also wipe the n8n data volume.

## Poke around

- **Fix Owen's case.** Log in to n8n at `localhost:5678` (`coordinator@example.com` / `Pantry-demo-1`), add "if the requested role doesn't fit, consider the other roles" to the system message in the screening node, and rerun `./demo.sh`. Compare Owen's two traces side by side: the prompt and the verdict are both captured per execution.
- **Send an edge case.** `curl -X POST localhost:5678/webhook/volunteer-signup -H 'Content-Type: application/json' -d '{"name":"Sam","age":17,"email":"sam@example.org","availability":"Saturday mornings","interests":"warehouse","notes":""}'`. A 17-year-old needs a guardian's consent noted; does the model ask for it?
- **Turn off content capture.** Set `N8N_OTEL_CAPTURE_INPUT=false` and `N8N_OTEL_CAPTURE_OUTPUT=false` in `docker-compose.yml` and recreate the container. The traces keep their shape but lose the form data, which you may need when applicants' personal details must not leave the server.
- **Trace only the model.** `N8N_OTEL_NODE_INCLUDE` limits which nodes become spans.

## Gotchas we hit

**The prompt and the verdict seem to be missing from the trace.** The Output column is empty and the LLM span has no output. Cause: `n8n-observability` records a node's data as span attributes, so Opik files them under the span's **Input**, as `n8n.node.input` and `n8n.node.output`. Fix: none needed. Open the `Screen volunteer` span's Input panel and look for those two keys.

**No usage, model or cost on the OpenAI node.** Every span is typed `general` and the cost column stays blank. Cause: with n8n 2.41.7 and n8n-observability 1.0.3, the OpenAI node's span carries no `gen_ai.*` usage attributes, and Opik only prices spans that have them. Fix: none from the workflow side. If you need cost, call the model from code with an Opik integration, or read usage in the OpenAI dashboard.

## How it's put together

- `Dockerfile`: `n8nio/n8n:2.41.7` plus `npm install -g n8n-observability@1.0.3`; sets `EXTERNAL_HOOK_FILES` to its hooks.
- `docker-compose.yml`: runs the image with the OTLP endpoint and headers that `setup.sh` computes. It also maps `host.docker.internal` so the container can reach an Opik running on the host.
- `workflow/volunteer-screening.json`: the exported workflow. The credential id is a placeholder that `setup.sh` fills at import time.
- `data/applicants.json`: four fictional sign-ups.
- `setup.sh`: headless bootstrap. It derives the OTLP endpoint from `OPIK_URL_OVERRIDE` (swapping `localhost` for `host.docker.internal`), adds `Authorization` only when `OPIK_API_KEY` is set, then runs compose up, owner setup, API key, credential, import and activate.
- `demo.sh`: posts each applicant to the webhook and prints the result.

---

<sub>built with [Opik](https://github.com/comet-ml/opik) · inspired by Opik's examples and documentation</sub>
