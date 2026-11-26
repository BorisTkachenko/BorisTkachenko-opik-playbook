package com.example.pharmacy;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import jakarta.enterprise.context.ApplicationScoped;

import java.util.List;
import java.util.stream.Collectors;

/** The RAG pipeline: retrieve the closest leaflet sections, then ask the model with them as context. */
@ApplicationScoped
public class FaqService {

    private final KnowledgeBase knowledgeBase;
    private final PharmacyAssistant assistant;

    public FaqService(KnowledgeBase knowledgeBase, PharmacyAssistant assistant) {
        this.knowledgeBase = knowledgeBase;
        this.assistant = assistant;
    }

    public String ask(String question) {
        List<EmbeddingMatch<TextSegment>> matches = knowledgeBase.search(question, 3);
        String context = matches.stream()
                .map(m -> "### " + m.embedded().metadata().getString("source") + "\n" + m.embedded().text())
                .collect(Collectors.joining("\n\n"));
        return assistant.answer(context.isEmpty() ? "(no matching leaflet sections)" : context, question);
    }
}
