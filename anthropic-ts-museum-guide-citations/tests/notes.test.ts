import { describe, expect, it } from "vitest";
import { buildSystemPrompt, extractQuotes, loadNotes, verifyQuotes } from "../src/notes.js";

const notes = loadNotes();

describe("notes", () => {
  it("loads every gallery file in order", () => {
    expect(notes.indexOf("Gallery 1")).toBeLessThan(notes.indexOf("Gallery 5"));
    expect(notes).toContain("Visitor Information");
  });

  it("puts the notes and the citation rule in the system prompt", () => {
    const prompt = buildSystemPrompt(notes);
    expect(prompt).toContain("<quote>");
    expect(prompt).toContain(notes.slice(0, 40));
  });

  it("extracts quotes, including multi-line ones", () => {
    expect(extractQuotes("a <quote>one</quote> b <quote>two\nlines</quote>")).toEqual(["one", "two\nlines"]);
  });

  it("accepts a quote that is really in the notes", () => {
    const [check] = verifyQuotes("<quote>built from 1,008 separate prisms of hand-polished crown glass</quote>", notes);
    expect(check?.verbatim).toBe(true);
  });

  it("rejects a paraphrased or invented quote", () => {
    const checks = verifyQuotes("<quote>made from about a thousand prisms</quote> <quote></quote>", notes);
    expect(checks.map((c) => c.verbatim)).toEqual([false, false]);
  });
});
