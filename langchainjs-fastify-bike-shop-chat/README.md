# langchainjs-fastify-bike-shop-chat

*A bike-shop chat widget on Fastify and LangChain.js, where every conversation reads as a transcript in Opik.*

![Node 20+](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![Fastify 5](https://img.shields.io/badge/fastify-5-000000?style=flat&logo=fastify&logoColor=white)
![opik-langchain 2.3.4](https://img.shields.io/badge/opik--langchain-2.3.4-2f54eb?style=flat)

A chat widget sends one HTTP request per message, so a customer who asks three questions leaves three unrelated rows in your tracing tool. The one you need when they complain ("it told me Sunday, then said you were open") is the whole conversation, in order, as plain sentences. This example is the backend for the widget on the site of Crankshaft Cycles, a made-up repair shop with prices, opening hours and a handful of open tune-up slots. It is built on Fastify with LangChain.js and traced with `opik-langchain`.

## What you'll build

- A Fastify server with `POST /chat` taking `{ message, sessionId }` and a small widget page served from the same process.
- A LangChain chain that takes the visitor's message as a **string** and returns the reply as a **string**. Inside it: load this session's history, look up facts in `data/shop.json` through a tool named `lookup_shop_info`, fill the prompt, call `gpt-4o-mini`, parse.
- One `OpikCallbackHandler` per session whose `threadId` is the widget's `sessionId`.
- `npm run demo`: boots the server on port 5451, plays three scripted visitor conversations over HTTP (booking a tune-up, opening hours, a flat tyre), shuts the server down and flushes. `npm run dev` is for you to chat in a browser.

The shop cannot book anything from chat. The prompt tells the bot to suggest open slots and send the customer to the phone number, and the demo shows it doing so.

## See it in Opik

Open the `langchainjs-fastify-bike-shop-chat` project. The demo produces 8 traces in 3 threads.

- **Threads tab.** Three rows: `visitor-tuneup-booking` (3 turns), `visitor-opening-hours` (2) and `visitor-flat-tyre` (3). Open one and you get the chat: the customer's sentence, the bot's sentence, next turn. For example the first turn of the booking thread reads "Hi! My commuter bike is making grinding noises. What tune-ups do you offer?" followed by the bot's list of Basic tune-up $59, Full tune-up $129 and E-bike service $149.
- **Traces tab.** Each turn is a trace named `bike-shop-turn`. Its input is only the visitor's message and its output only the bot's reply. That is what lets the thread view read like a transcript.
- **Inside one trace** there are 7 spans: `load-session-history`, `retrieve-facts`, and under it `lookup_shop_info` (type `tool`) holding the query and the facts it found; then `ChatPromptTemplate`, `ChatOpenAI` (type `llm`) and `StrOutputParser`. Open `ChatOpenAI` to see the model `gpt-4o-mini`, a few hundred tokens and a cost around $0.00006 per turn, and the exact prompt with the retrieved facts spliced into the system message.
- Compare the second turn of the opening-hours thread ("Okay, what about Thursday evening?") with its `lookup_shop_info` input: the query includes the previous message, which is why the hours document is found even though the follow-up never says "open".

## Run it yourself

1. `cd langchainjs-fastify-bike-shop-chat && npm install`
2. Put `OPENAI_API_KEY` in a `.env` (copy `.env.example`) or in a `.env` further up the tree; the app loads both. For a local self-hosted Opik, also set `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`; for Opik Cloud set `OPIK_API_KEY` and your workspace instead.
3. `npm run demo` (about 15 seconds, a fraction of a cent).
4. `npm run verify` reads the project back through Opik's REST API and checks that every root is plain text, every turn has a retrieval tool span, and the LLM spans carry usage and cost.
5. `npm run dev`, open http://localhost:3000, and chat. Each browser tab is its own session and its own thread.

Tests are offline: `OPIK_TRACK_DISABLE=true npm test` (no keys needed; the variable switches the Opik SDK to a no-op).

## Poke around

- Open the widget in two tabs and ask the same question in both. Two sessions, two threads, and the second tab's bot knows nothing about the first.
- Ask for something the data does not cover ("do you fix skateboards?"). Open the trace: `lookup_shop_info` returns "no matching facts" and the bot falls back to the phone number.
- Change the root so it takes `{ messages: [...] }` instead of a string and look at the Threads tab again. The rows stop being sentences.
- Delete `threadId: sessionId` in `src/tracing.ts` and rerun the demo: the same 8 traces appear with no threads.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-langchain@2.3.4`.** `opik-langchain` declares a stale peer range for `opik`, so npm refuses to install the matching `opik` 2.3.4. Pin one `opik` for the whole tree with an override:

```json
"dependencies": { "opik": "2.3.4", "opik-langchain": "2.3.4" },
"overrides": { "opik": "$opik" }
```

**Trace input and output look like `{"input": {"value": "..."}}`, not a bare string.** That is how the callback handler stores a string-in, string-out chain, and it is what the Threads view renders as text. If your root run takes or returns message arrays or dicts, the thread rows show JSON. `scripts/verify.ts` checks for this exact shape.

**Traces missing after the process exits.** The SDK batches in memory. `demo.ts` closes the server first and then awaits `opikClient.flush()`; `server.ts` flushes on SIGINT/SIGTERM so Ctrl+C does not drop the last turns.

## How it's put together

- `src/shop.ts`: loads `data/shop.json`, builds one small document per service, hours, slots and policy, and ranks them by keyword overlap.
- `src/chat.ts`: the string-in, string-out chain, the `lookup_shop_info` tool, per-session history.
- `src/tracing.ts`: the one Opik client, the per-session handler with `threadId`, and `flushOpik`.
- `src/server.ts`: Fastify app, `POST /chat`, static widget; the model is injectable for tests.
- `src/demo.ts`: boots the server, plays the scripted conversations over HTTP, closes it, flushes.
- `scripts/verify.ts`: reads traces, threads, spans, usage and cost back from Opik.
- `public/index.html`: the widget, one `sessionId` per tab.
- `data/shop.json`: the fictional shop.
- `tests/shop.test.ts`, `tests/chat.test.ts`: retrieval, follow-up queries, the chain with a fake model, the traced chain with tracking disabled, and the HTTP route via `inject`.

---

*built with Opik · inspired by Opik's examples and documentation*
