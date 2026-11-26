/**
 * Shop knowledge: loads the fictional shop data and answers "which facts are
 * relevant to this question?" with a tiny keyword retriever.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

export interface ShopData {
  shop: string;
  address: string;
  phone: string;
  hours: Record<string, string>;
  services: { name: string; price: number; turnaround: string; includes: string }[];
  policies: string[];
  openSlots: string[];
}

export interface Doc {
  id: string;
  text: string;
}

export function loadShop(file = path.join(here, "../data/shop.json")): ShopData {
  return JSON.parse(readFileSync(file, "utf8")) as ShopData;
}

/** One small document per fact group, so retrieval returns focused snippets. */
export function buildDocs(shop: ShopData): Doc[] {
  const docs: Doc[] = shop.services.map((s) => ({
    id: `service:${s.name.toLowerCase().replace(/\s+/g, "-")}`,
    text: `${s.name} costs $${s.price}. Turnaround: ${s.turnaround}. Includes: ${s.includes}.`,
  }));
  docs.push({
    id: "hours",
    text:
      `Opening hours of ${shop.shop} (${shop.address}, phone ${shop.phone}): ` +
      Object.entries(shop.hours)
        .map(([day, h]) => `${day} ${h}`)
        .join(", ") +
      ".",
  });
  docs.push({
    id: "slots",
    text: `Open drop-off slots this week for booking a tune-up or repair: ${shop.openSlots.join(", ")}.`,
  });
  shop.policies.forEach((p, i) => docs.push({ id: `policy:${i + 1}`, text: p }));
  return docs;
}

const STOP = new Set(
  "a an the is are do does i my me you your can for to of in on at and or it its how what when much about with be there any".split(" ")
);

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+/g) ?? [])
    .filter((t) => !STOP.has(t))
    .map((t) => (t.length > 3 && t.endsWith("s") ? t.slice(0, -1) : t));
}

// Words visitors use that the data words differently.
const SYNONYMS: Record<string, string[]> = {
  open: ["hour", "closed"],
  close: ["hour", "closed"],
  weekend: ["saturday", "sunday"],
  book: ["slot", "booking"],
  appointment: ["slot", "booking"],
  schedule: ["slot", "booking"],
  puncture: ["flat", "tyre"],
  ebike: ["e", "bosch", "shimano"],
  battery: ["e", "bosch"],
};

/** Rank docs by keyword overlap with the query; return the best `k` (never zero-score docs). */
export function retrieve(docs: Doc[], query: string, k = 3): Doc[] {
  const terms = new Set<string>();
  for (const t of tokenize(query)) {
    terms.add(t);
    (SYNONYMS[t] ?? []).forEach((s) => terms.add(s));
  }
  return docs
    .map((doc) => {
      const words = new Set(tokenize(doc.text));
      let score = 0;
      for (const t of terms) if (words.has(t)) score += 1;
      return { doc, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((x) => x.doc);
}
