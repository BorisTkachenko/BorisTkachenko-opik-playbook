import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const DOCS_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..", "docs");

/** Concatenate every file in docs/ into one block of exhibit notes (small enough to fit in the prompt). */
export function loadNotes(dir: string = DOCS_DIR): string {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .map((f) => readFileSync(join(dir, f), "utf8").trim())
    .join("\n\n");
}

export function buildSystemPrompt(notes: string, lax = false): string {
  // lax: a deliberately sloppy prompt, used to show the test suite catching a regression.
  if (lax) {
    return `You are the friendly audio guide at the Pellwick Lamp Museum. Chat with visitors \
about lighthouses and the exhibits, drawing on the notes below and anything else you know.

<exhibit_notes>
${notes}
</exhibit_notes>`;
  }
  return `You are the audio guide at the Pellwick Lamp Museum. Visitors ask you \
questions about the exhibits; you answer from the exhibit notes below and from nothing else.

Rules:
- Answer only from the exhibit notes. If the notes do not cover the question, say \
plainly that you do not know, and do not guess or use outside knowledge.
- Every factual claim must be backed by a citation: a verbatim excerpt from the notes \
wrapped in <quote>...</quote> tags, copied character for character from a single sentence.
- Keep it short, as if spoken aloud: the answer first, then the supporting quote(s).

<exhibit_notes>
${notes}
</exhibit_notes>`;
}

export function extractQuotes(answer: string): string[] {
  return [...answer.matchAll(/<quote>([\s\S]*?)<\/quote>/g)].map((m) => (m[1] ?? "").trim());
}

const squash = (s: string) => s.replace(/\*\*/g, "").replace(/\s+/g, " ").trim();

export interface QuoteCheck {
  quote: string;
  verbatim: boolean;
}

/** Deterministic citation check: is each quoted excerpt literally present in the notes? */
export function verifyQuotes(answer: string, notes: string): QuoteCheck[] {
  const haystack = squash(notes);
  return extractQuotes(answer).map((quote) => ({
    quote,
    verbatim: quote.length > 0 && haystack.includes(squash(quote)),
  }));
}
