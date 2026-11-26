package com.example.pharmacy;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.api.trace.Span;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("/ask")
public class FaqResource {

    private final ObjectMapper json = new ObjectMapper();
    private final FaqService faq;

    public FaqResource(FaqService faq) {
        this.faq = faq;
    }

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String ask(@QueryParam("q") String question) {
        String answer = faq.ask(question);
        // Span.current() is Quarkus's HTTP server span, the root of the Opik trace. Opik leaves a trace's
        // Input/Output empty unless the root span carries `input`/`output` attributes, so set them here.
        Span root = Span.current();
        root.setAttribute("input", json.createObjectNode().put("question", question).toString());
        root.setAttribute("output", json.createObjectNode().put("answer", answer).toString());
        return answer;
    }
}
