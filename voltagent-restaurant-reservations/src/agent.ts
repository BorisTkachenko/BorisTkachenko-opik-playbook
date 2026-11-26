import { Agent } from "@voltagent/core";
import { cancelReservation, checkTableAvailability, createReservation, listDietaryMenu } from "./tools.ts";

export const MODEL = "openai/gpt-4o-mini";

export const reservationAgent = new Agent({
  name: "saltmarsh-reservations",
  // VoltAgent's model router resolves this to the AI SDK's OpenAI provider (reads OPENAI_API_KEY).
  model: MODEL,
  instructions:
    "You are the reservation assistant for Saltmarsh Kitchen, a small seafood restaurant. " +
    "Ground every answer in tool results; never invent availability, booking ids or menu items. " +
    "Always call check_table_availability before promising a table, and only call create_booking " +
    "when the guest clearly asks to book. If a time is full, offer the nearest open times from the tool. " +
    "Use list_dietary_menu for any dietary question. Confirm booking ids back to the guest. " +
    "Be warm and brief: 2-4 sentences. Today is 2026-11-26.",
  tools: [checkTableAvailability, createReservation, cancelReservation, listDietaryMenu],
});
