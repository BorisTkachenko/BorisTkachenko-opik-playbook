// The four reservation tools. Thin zod wrappers over src/restaurant.ts; none
// of them knows tracing exists.
import { createTool } from "@voltagent/core";
import { z } from "zod";
import { cancelBooking, checkAvailability, createBooking, dietaryItems } from "./restaurant.ts";

export const checkTableAvailability = createTool({
  name: "check_table_availability",
  description: "Check which tables are free for a date, seating time and party size. Returns nearest open times when full.",
  parameters: z.object({
    date: z.string().describe("YYYY-MM-DD"),
    time: z.string().describe("24h HH:MM on the half hour, 17:00-21:00"),
    party_size: z.number().int().min(1).max(8),
  }),
  execute: async ({ date, time, party_size }) => checkAvailability(date, time, party_size),
});

export const createReservation = createTool({
  name: "create_booking",
  description: "Book a table. Only call after check_table_availability showed a free table and the guest asked to book.",
  parameters: z.object({
    name: z.string().describe("Surname or name for the booking"),
    date: z.string().describe("YYYY-MM-DD"),
    time: z.string().describe("24h HH:MM"),
    party_size: z.number().int().min(1).max(8),
  }),
  execute: async ({ name, date, time, party_size }) => createBooking(name, date, time, party_size),
});

export const cancelReservation = createTool({
  name: "cancel_booking",
  description: "Cancel an existing booking by its id (e.g. BK-1004).",
  parameters: z.object({ booking_id: z.string() }),
  execute: async ({ booking_id }) => cancelBooking(booking_id),
});

export const listDietaryMenu = createTool({
  name: "list_dietary_menu",
  description: "List menu items that suit a dietary need: vegan, vegetarian, gluten-free or dairy-free. Optional course filter.",
  parameters: z.object({
    diet: z.enum(["vegan", "vegetarian", "gluten-free", "dairy-free"]),
    course: z.enum(["starter", "main", "dessert"]).optional(),
  }),
  execute: async ({ diet, course }) => dietaryItems(diet, course),
});
