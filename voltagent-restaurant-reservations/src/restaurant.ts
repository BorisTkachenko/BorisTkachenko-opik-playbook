// Pure reservation logic for Saltmarsh Kitchen, a fictional restaurant. All
// data comes from data/restaurant.json and bookings mutate in memory only, so
// every demo run starts from the same state and nothing leaves the machine.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export type Table = { id: string; seats: number };
export type Booking = { id: string; name: string; date: string; time: string; party_size: number; table_id: string };
export type MenuItem = { item: string; course: string; price_usd: number; dietary: string[] };

type Data = {
  name: string;
  service: { open: string; last_seating: string; stay_minutes: number; slot_minutes: number };
  tables: Table[];
  bookings: Booking[];
  menu: MenuItem[];
};

const load = (): Data =>
  JSON.parse(readFileSync(fileURLToPath(new URL("../data/restaurant.json", import.meta.url)), "utf8"));

let data: Data = load();
let nextId = 2001;

/** Reset to the pristine data file (used by tests and between demo runs). */
export function resetRestaurant(): void {
  data = load();
  nextId = 2001;
}

export const toMinutes = (hhmm: string): number => {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

const validTime = (time: string): boolean => {
  const { open, last_seating, slot_minutes } = data.service;
  const t = toMinutes(time);
  return /^\d{2}:\d{2}$/.test(time) && t >= toMinutes(open) && t <= toMinutes(last_seating) && (t - toMinutes(open)) % slot_minutes === 0;
};

// Two bookings clash when their stay windows overlap on the same table and date.
const clashes = (b: Booking, date: string, time: string): boolean => {
  const stay = data.service.stay_minutes;
  const start = toMinutes(time);
  const bStart = toMinutes(b.time);
  return b.date === date && start < bStart + stay && bStart < start + stay;
};

/** Smallest free table that fits the party, or the full list of options. */
export function freeTables(date: string, time: string, partySize: number): Table[] {
  return data.tables
    .filter((t) => t.seats >= partySize)
    .filter((t) => !data.bookings.some((b) => b.table_id === t.id && clashes(b, date, time)))
    .sort((a, b) => a.seats - b.seats);
}

export function checkAvailability(date: string, time: string, partySize: number) {
  if (!validTime(time)) {
    const { open, last_seating } = data.service;
    return { available: false, error: `Seatings run ${open}-${last_seating} on the half hour.` };
  }
  const tables = freeTables(date, time, partySize);
  if (tables.length > 0) return { available: true, date, time, party_size: partySize, tables: tables.map((t) => ({ id: t.id, seats: t.seats })) };
  // Nothing free: suggest the nearest open seatings that day so the agent can offer them.
  const { open, last_seating, slot_minutes } = data.service;
  const alternatives: string[] = [];
  for (let m = toMinutes(open); m <= toMinutes(last_seating); m += slot_minutes) {
    const hhmm = `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
    if (freeTables(date, hhmm, partySize).length > 0) alternatives.push(hhmm);
  }
  alternatives.sort((a, b) => Math.abs(toMinutes(a) - toMinutes(time)) - Math.abs(toMinutes(b) - toMinutes(time)));
  return { available: false, date, time, party_size: partySize, nearest_open_times: alternatives.slice(0, 3) };
}

export function createBooking(name: string, date: string, time: string, partySize: number) {
  if (!validTime(time)) return { error: "Invalid seating time." };
  const table = freeTables(date, time, partySize)[0];
  if (!table) return { error: "No table free at that time; check availability first." };
  const booking: Booking = { id: `BK-${nextId++}`, name, date, time, party_size: partySize, table_id: table.id };
  data.bookings.push(booking);
  return { confirmed: true, booking };
}

export function cancelBooking(id: string) {
  const index = data.bookings.findIndex((b) => b.id.toLowerCase() === id.trim().toLowerCase());
  if (index < 0) return { cancelled: false, error: `No booking ${id}.` };
  const [removed] = data.bookings.splice(index, 1);
  return { cancelled: true, booking: removed };
}

export function dietaryItems(diet: string, course?: string) {
  const wanted = diet.trim().toLowerCase();
  const items = data.menu
    .filter((m) => m.dietary.includes(wanted))
    .filter((m) => !course || m.course === course.toLowerCase());
  return { diet: wanted, count: items.length, items };
}

export const restaurantName = (): string => data.name;
export const bookingsOn = (date: string): Booking[] => data.bookings.filter((b) => b.date === date);
