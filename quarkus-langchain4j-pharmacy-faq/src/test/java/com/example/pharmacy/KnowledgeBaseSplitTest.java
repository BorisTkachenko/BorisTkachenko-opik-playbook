package com.example.pharmacy;

import dev.langchain4j.data.segment.TextSegment;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Offline tests for the leaflet chunker: plain JUnit, no Quarkus boot, no OpenAI key and no Opik.
 * Run with: mvn test
 */
class KnowledgeBaseSplitTest {

    @Test
    void splitsOneChunkPerSectionPrefixedWithTheTitle(@TempDir Path dir) throws IOException {
        Path leaflet = dir.resolve("demo.md");
        Files.writeString(leaflet, """
                # Demoxin 10 mg (test leaflet)

                Intro line under the title.

                ## Dosage notes
                Take one tablet daily.

                ## Interactions
                Avoid grapefruit juice.
                """);

        List<TextSegment> chunks = KnowledgeBase.split(leaflet);

        assertEquals(3, chunks.size());
        assertTrue(chunks.get(1).text().startsWith("Demoxin 10 mg (test leaflet) / Dosage notes\n"));
        assertTrue(chunks.get(2).text().contains("Avoid grapefruit juice."));
        assertEquals("demo.md", chunks.get(2).metadata().getString("source"));
    }

    @Test
    void skipsEmptySections(@TempDir Path dir) throws IOException {
        Path leaflet = dir.resolve("empty.md");
        Files.writeString(leaflet, "# Title only\n\n## Empty heading\n\n## Filled\nSomething.\n");

        List<TextSegment> chunks = KnowledgeBase.split(leaflet);

        assertEquals(1, chunks.size());
        assertTrue(chunks.get(0).text().startsWith("Title only / Filled"));
    }

    @Test
    void everyShippedLeafletProducesChunksThatNameTheirSource() throws IOException {
        try (Stream<Path> files = Files.list(Path.of("docs"))) {
            for (Path leaflet : files.filter(p -> p.toString().endsWith(".md")).toList()) {
                List<TextSegment> chunks = KnowledgeBase.split(leaflet);
                assertFalse(chunks.isEmpty(), leaflet + " produced no chunks");
                for (TextSegment chunk : chunks) {
                    assertEquals(leaflet.getFileName().toString(), chunk.metadata().getString("source"));
                }
            }
        }
    }
}
