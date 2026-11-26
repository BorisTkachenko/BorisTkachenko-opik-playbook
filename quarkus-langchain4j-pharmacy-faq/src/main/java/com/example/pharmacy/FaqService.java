package com.example.pharmacy;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import jakarta.enterprise.context.ApplicationScoped;

import java.util.List;
import java.util.stream.Collectors;

/** The RAG pipeline: retrieve the closest leaflet sections, then ask the model with them as context. */
@ApplicationScoped
public class FaqService {

    private static final int TOP_K = 3;
    private final ObjectMapper json = new ObjectMapper();

    private final KnowledgeBase knowledgeBase;
    private final PharmacyAssistant assistant;
    private final Tracer tracer;

    public FaqService(KnowledgeBase knowledgeBase, PharmacyAssistant assistant, Tracer tracer) {
        this.knowledgeBase = knowledgeBase;
        this.assistant = assistant;
        this.tracer = tracer;
    }

    public String ask(String question) {
        List<EmbeddingMatch<TextSegment>> matches = retrieve(question);
        String context = matches.stream()
                .map(m -> "### " + m.embedded().metadata().getString("source") + "\n" + m.embedded().text())
                .collect(Collectors.joining("\n\n"));
        return assistant.answer(context.isEmpty() ? "(no matching leaflet sections)" : context, question);
    }

    /**
     * Retrieval gets its own span: LangChain4j does not trace the vector search, so without this the
     * trace tree would show an embeddings HTTP call and then the model, with no record of WHICH
     * leaflet sections were retrieved. Opik maps the span attributes named `input` and `output` to
     * the span's Input and Output panels (a plain `general` span).
     */
    private List<EmbeddingMatch<TextSegment>> retrieve(String question) {
        Span span = tracer.spanBuilder("retrieve_leaflets").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            span.setAttribute("input", json.createObjectNode().put("query", question).put("top_k", TOP_K).toString());
            List<EmbeddingMatch<TextSegment>> matches = knowledgeBase.search(question, TOP_K);
            ObjectNode out = json.createObjectNode();
            ArrayNode chunks = out.putArray("chunks");
            for (EmbeddingMatch<TextSegment> m : matches) {
                chunks.addObject()
                        .put("source", m.embedded().metadata().getString("source"))
                        .put("score", Math.round(m.score() * 1000) / 1000.0)
                        .put("text", m.embedded().text());
            }
            span.setAttribute("output", out.toString());
            return matches;
        } finally {
            span.end();
        }
    }
}
