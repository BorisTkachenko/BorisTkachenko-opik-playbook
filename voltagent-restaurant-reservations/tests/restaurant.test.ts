import { beforeEach, describe, expect, it } from "vitest";
import { bookingsOn, cancelBooking, checkAvailability, createBooking, dietaryItems, resetRestaurant } from "../src/restaurant.ts";
import { checkTableAvailability, createReservation } from "../src/tools.ts";

beforeEach(resetRestaurant);

describe("reservation logic", () => {
  it("reports a full house with the nearest open times", () => {
    const r: any = checkAvailability("2026-12-05", "19:00", 4);
    expect(r.available).toBe(false);
    expect(r.nearest_open_times).toHaveLength(3);
    expect(r.nearest_open_times[0]).toBe("18:00");
  });

  it("books the smallest table that fits and blocks a clashing booking", () => {
    const first: any = createBooking("Alvarez", "2026-12-05", "21:00", 4);
    expect(first.booking).toMatchObject({ id: "BK-2001", table_id: "T3" });
    const second: any = createBooking("Ng", "2026-12-05", "21:00", 4);
    expect(second.booking.table_id).toBe("T4");
    // T3 and T4 are now taken for the 21:00 stay, so only the bigger tables remain.
    expect((checkAvailability("2026-12-05", "21:00", 4) as any).tables.map((t: any) => t.id)).toEqual(["T5", "T6"]);
  });

  it("rejects off-grid times and cancels by id, case-insensitively, in memory only", () => {
    expect(checkAvailability("2026-12-05", "19:10", 2)).toHaveProperty("error");
    expect(cancelBooking("bk-1004")).toMatchObject({ cancelled: true });
    expect(bookingsOn("2026-12-05")).toHaveLength(5);
    resetRestaurant();
    expect(bookingsOn("2026-12-05")).toHaveLength(6);
    expect(cancelBooking("BK-9999")).toMatchObject({ cancelled: false });
  });

  it("filters the menu by diet and course", () => {
    const r = dietaryItems("vegan", "main");
    expect(r.items.map((i) => i.item)).toEqual(["Roast cauliflower steak with tahini"]);
    expect(dietaryItems("gluten-free").count).toBeGreaterThan(5);
  });
});

describe("tools with tracing disabled", () => {
  // OTEL_SDK_DISABLED=true is OpenTelemetry's switch for turning the SDK off. The tools carry no
  // tracing code of their own, so they run the same with it set: spans only exist inside an agent run.
  it("execute directly, no Opik or model involved", async () => {
    process.env.OTEL_SDK_DISABLED = "true";
    const avail: any = await (checkTableAvailability as any).execute({ date: "2026-12-06", time: "18:00", party_size: 2 });
    expect(avail.available).toBe(true);
    const booked: any = await (createReservation as any).execute({ name: "Kim", date: "2026-12-06", time: "20:00", party_size: 2 });
    expect(booked.confirmed).toBe(true);
  });
});
