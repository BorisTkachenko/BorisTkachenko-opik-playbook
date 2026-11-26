# quarkus-langchain4j-pharmacy-faq

![Java 21+](https://img.shields.io/badge/java-21%2B-ED8B00?style=flat&logo=openjdk&logoColor=white)
![Quarkus 3.40](https://img.shields.io/badge/quarkus-3.40-4695EB?style=flat&logo=quarkus&logoColor=white)
![LangChain4j 1.15](https://img.shields.io/badge/quarkus--langchain4j-1.15-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/Opik-OTLP-2f54eb?style=flat)](https://github.com/comet-ml/opik)

**A pharmacy "can I take this with that?" bot on Quarkus, whose every answer shows up in Opik as a trace, with no Opik library in the JVM.**

A medication FAQ is a bad place for a silent mistake. When the bot tells a customer how long a course lasts or what
not to mix with their blood-pressure tablets, you want to see which leaflet text it was handed and what the model did
with it. The JVM has no Opik SDK, but Quarkus already speaks OpenTelemetry and Opik ingests OTLP directly, so the
integration is one extension, a handful of properties and two switches that are off by default.

## What you'll build

A Quarkus service for a fictional chain, Larkspur Pharmacies, with one endpoint: `GET /ask?q=...`. At startup it reads
six fictional leaflets from `docs/` (invented medicines such as Veltrazine, Corvadol and Brelovan: doses,
interactions, storage, plus opening hours and a "when to ask a pharmacist" page), splits them by section into 22
chunks, embeds them with `text-embedding-3-small` and keeps them in LangChain4j's in-memory store. Each question
retrieves the three closest sections, and a LangChain4j AI service on `gpt-4o-mini` answers from those sections only.
Its system prompt sends pregnancy, emergencies and anything missing from the leaflets to the pharmacist line instead
of guessing.

`./run.sh` builds the jar, starts it on port 5581, asks five scripted questions over HTTP, stops it and exits.

## See it in Opik

Open the **quarkus-langchain4j-pharmacy-faq** project and the **Traces** tab. One run leaves six traces: five
named `GET /ask`, one per question, and one `index_leaflets` from startup (22 sections indexed, one embeddings call).

Click the first `GET /ask` (the Veltrazine dose and storage question). The tree reads:

- `GET /ask` is the Quarkus HTTP server span. The trace's Input holds the question; its Output holds the answer.
- `retrieve_leaflets` is the retrieval step. Input is the query and `top_k: 3`. Output is the three chunks with their
  source file and similarity score; the best was 0.834, a `veltrazine.md` storage section, with the dosage section
  right behind it at 0.815. A `POST /embeddings` span sits under it.
- `langchain4j.aiservices.PharmacyAssistant.answer` is the AI-service call. Under it, `completion gpt-4o-mini` is the
  one span of type **llm**. Its Input is the system prompt plus the leaflet extracts plus the question; its Output is
  the answer. Opik reads model `gpt-4o-mini`, provider `openai`, 378 prompt + 42 completion = 420 tokens, and an
  estimated cost of $0.0000819 (Opik computes this from the usage and its price table). A `POST` HTTP span for the
  OpenAI call is nested inside it.

Compare the other four. The Sunday-hours question retrieves `pharmacy-services.md` and answers "open at 10:00". The
pregnancy question uses 402 tokens and gets "I cannot answer that. Please talk to your pharmacist at 0800 555 0142."
When an answer is wrong you can tell in one click whether retrieval fetched the wrong sections or the model ignored
the right ones.

What does not show up as you might expect: the trace's Input is not just the question, because the HTTP server
attributes (user agent, route, status code) are folded into it alongside `question`. Only the llm span has token
usage; the other spans are type `general`.

## Run it yourself

1. Put `OPENAI_API_KEY` in `.env` in this folder or any parent folder (copy `.env.example`). Opik settings
   (`OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE`) are read from the same file; for a local Opik they are
   `http://localhost:5173/api/` and `default`.
2. `./run.sh` (needs Java 21+ and Maven; Quarkus Dev Services are disabled, so no Docker is involved).
   It runs `mvn -q -DskipTests package`, starts `target/quarkus-app/quarkus-run.jar`, prints each question and
   answer, and stops the service. A full run takes about 20 seconds and a few hundredths of a cent.
3. Open the project named above in Opik.
4. To keep the service up and ask your own questions:
   `PHARMACY_PORT=5581 java -jar target/quarkus-app/quarkus-run.jar`, then
   `curl --get --data-urlencode "q=Can I take Corvadol with Thinnex?" http://localhost:5581/ask`.
   Spans are exported in batches every five seconds, and the rest flush when the service stops.

## Poke around

- Ask something the leaflets do not cover ("Is Veltrazine safe for my dog?"). Open `retrieve_leaflets`: the chunks are
  loosely related at best, and the answer should point you to the pharmacist line.
- Change `TOP_K` in `FaqService` from 3 to 1 and ask the Corvadol-with-Brelovan question. The retrieval output shrinks
  to one chunk; compare the llm span's prompt tokens with the original run.
- Set the two `quarkus.langchain4j.tracing.include-*` switches to `false` and rerun. The llm span keeps its model,
  tokens and cost but loses its Input and Output text.
- Raise `minScore` in `KnowledgeBase.search` to 0.6 and ask the Sunday-hours question. If nothing clears the bar the
  prompt says "(no matching leaflet sections)", visible in the llm span's Input.

## Gotchas we hit

**Nothing arrives in Opik and the app logs no error.** Quarkus appends `/v1/traces` to the OTLP endpoint itself. Giving
it Opik's full traces URL sends the data to `.../otel/v1/traces/v1/traces`; the failure is logged only at `FINE`
("Exporter failed"). Configure the base URL:

```properties
quarkus.otel.exporter.otlp.traces.endpoint=http://localhost:5173/api/v1/private/otel
quarkus.otel.exporter.otlp.traces.protocol=http/protobuf
quarkus.otel.exporter.otlp.traces.headers=Comet-Workspace=default,projectName=quarkus-langchain4j-pharmacy-faq
```

**Startup warns `Unrecognized configuration key "quarkus.otel.exporter.otlp.traces.endpoint"`.** The `quarkus.otel.*`
keys only exist once `io.quarkus:quarkus-opentelemetry` is on the classpath; without it Quarkus ignores them and
exports nothing. Add the dependency.

**The llm span arrives with usage and cost but an empty Input and Output.** LangChain4j keeps prompt and completion
text off spans by default. Turn them on:

```properties
quarkus.langchain4j.tracing.include-prompt=true
quarkus.langchain4j.tracing.include-completion=true
```

**The trace's Input and Output columns hold HTTP attributes, or nothing.** Opik takes them from the root span, and the
Quarkus server span only carries HTTP attributes. Set `input` and `output` attributes on `Span.current()` in the
resource method (see `FaqResource`). The same names on a span you create yourself, as `retrieve_leaflets` does, fill
that span's Input and Output.

**Cost.** Nothing to map here: the llm span carries the `openai` provider, so Opik prices it from the token usage. If
you point Quarkus at a different provider, check the span shows a provider before expecting a cost.

## How it's put together

- `pom.xml`: Quarkus 3.40.1.1, `quarkus-langchain4j-openai` 1.15.1, `quarkus-rest-jackson`, `quarkus-opentelemetry`.
- `src/main/resources/application.properties`: models, port, the OTLP export to Opik, and the two content switches.
- `src/main/java/com/example/pharmacy/PharmacyAssistant.java`: the AI service interface with the pharmacist-fallback prompt.
- `.../KnowledgeBase.java`: reads `docs/`, splits by section, embeds and searches; startup indexing runs in an `index_leaflets` span.
- `.../FaqService.java`: retrieve then answer, with the `retrieve_leaflets` span.
- `.../FaqResource.java`: the `/ask` endpoint; stamps question and answer on the trace root.
- `docs/`: the fictional leaflets. `questions.txt`: the scripted questions. `run.sh`: build, boot, ask, stop.
- No tests: this example is Java and ships none; `mvn -q package` must pass.

---

*built with Opik · inspired by Opik's examples and documentation*
