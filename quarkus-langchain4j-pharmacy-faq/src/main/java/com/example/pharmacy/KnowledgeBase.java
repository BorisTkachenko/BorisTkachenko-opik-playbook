package com.example.pharmacy;

import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/** Loads docs/*.md at startup, splits them by section and keeps them in an in-memory vector store. */
@ApplicationScoped
public class KnowledgeBase {

    private static final Logger LOG = Logger.getLogger(KnowledgeBase.class);

    private final EmbeddingModel embeddingModel;
    private final InMemoryEmbeddingStore<TextSegment> store = new InMemoryEmbeddingStore<>();
    private final Path docsDir;
    private final Tracer tracer;

    public KnowledgeBase(EmbeddingModel embeddingModel, Tracer tracer,
                         @ConfigProperty(name = "pharmacy.docs-dir", defaultValue = "docs") String docsDir) {
        this.embeddingModel = embeddingModel;
        this.tracer = tracer;
        this.docsDir = Path.of(docsDir);
    }

    void ingest(@Observes StartupEvent event) throws IOException {
        List<TextSegment> segments = new ArrayList<>();
        try (Stream<Path> files = Files.list(docsDir)) {
            for (Path file : files.filter(p -> p.toString().endsWith(".md")).sorted().toList()) {
                segments.addAll(split(file));
            }
        }
        // Startup indexing is not an HTTP request, so give it its own root span; otherwise the
        // embeddings call would arrive in Opik as an anonymous "POST /embeddings" trace.
        Span span = tracer.spanBuilder("index_leaflets").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            span.setAttribute("input", "{\"docs_dir\": \"" + docsDir + "\"}");
            List<Embedding> embeddings = embeddingModel.embedAll(segments).content();
            store.addAll(embeddings, segments);
            span.setAttribute("output", "{\"sections_indexed\": " + segments.size() + "}");
        } finally {
            span.end();
        }
        LOG.infof("Indexed %d leaflet sections from %s", segments.size(), docsDir);
    }

    /** One chunk per "## " section, each prefixed with the document title so it stands alone. */
    static List<TextSegment> split(Path file) throws IOException {
        List<TextSegment> out = new ArrayList<>();
        String title = "";
        String heading = "";
        StringBuilder body = new StringBuilder();
        for (String line : Files.readAllLines(file)) {
            if (line.startsWith("## ") || line.startsWith("# ")) {
                flush(out, file, title, heading, body);
                if (line.startsWith("# ")) {
                    title = line.substring(2);
                    heading = "";
                } else {
                    heading = line.substring(3);
                }
            } else {
                body.append(line).append('\n');
            }
        }
        flush(out, file, title, heading, body);
        return out;
    }

    private static void flush(List<TextSegment> out, Path file, String title, String heading, StringBuilder body) {
        String text = body.toString().strip();
        if (!text.isEmpty()) {
            String full = title + (heading.isEmpty() ? "" : " / " + heading) + "\n" + text;
            out.add(TextSegment.from(full, dev.langchain4j.data.document.Metadata.from("source", file.getFileName().toString())));
        }
        body.setLength(0);
    }

    public List<EmbeddingMatch<TextSegment>> search(String question, int topK) {
        Embedding query = embeddingModel.embed(question).content();
        return store.search(EmbeddingSearchRequest.builder()
                .queryEmbedding(query).maxResults(topK).minScore(0.2).build()).matches();
    }
}
