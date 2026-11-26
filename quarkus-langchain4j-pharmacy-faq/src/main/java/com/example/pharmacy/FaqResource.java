package com.example.pharmacy;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("/ask")
public class FaqResource {

    private final FaqService faq;

    public FaqResource(FaqService faq) {
        this.faq = faq;
    }

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String ask(@QueryParam("q") String question) {
        return faq.ask(question);
    }
}
