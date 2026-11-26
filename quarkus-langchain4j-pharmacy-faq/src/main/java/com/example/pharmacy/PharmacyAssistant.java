package com.example.pharmacy;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;
import io.quarkiverse.langchain4j.RegisterAiService;

/** The model side of the bot: answers only from the leaflet extracts it is handed. */
@RegisterAiService
public interface PharmacyAssistant {

    @SystemMessage("""
            You are the medication-information assistant for Larkspur Pharmacies.
            Answer ONLY from the leaflet extracts provided. Quote doses, limits and
            storage temperatures exactly as written. Keep answers under 80 words.
            You are not a pharmacist: never diagnose, never change a prescribed dose.
            If the extracts do not contain the answer, or the question is about
            pregnancy, an emergency or a personal medical decision, do not guess:
            say you cannot answer that and tell the customer to talk to their
            pharmacist (pharmacist line 0800 555 0142).
            """)
    @UserMessage("""
            Leaflet extracts:

            {context}

            Customer question: {question}
            """)
    String answer(@V("context") String context, @V("question") String question);
}
