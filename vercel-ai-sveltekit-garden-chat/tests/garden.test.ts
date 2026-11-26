import { describe, expect, it } from "vitest";
import { buildSystemPrompt, parseGuide, retrieve, tokenize } from "../src/lib/server/garden";
import fs from "node:fs";

const sections = parseGuide(fs.readFileSync("data/garden-guide.md", "utf8"));

describe("garden guide retrieval", () => {
  it("splits the guide into titled sections", () => {
    expect(sections.length).toBeGreaterThanOrEqual(8);
    expect(sections[0].title).toBe("Planting calendar: cool season");
    expect(sections.every((s) => s.body.length > 50)).toBe(true);
  });

  it("drops stop words and short tokens", () => {
    expect(tokenize("When can I plant the tomatoes?")).toEqual(["when", "plant", "tomatoes"].filter((w) => w !== "when"));
  });

  it("finds the slug section for a slug question", () => {
    expect(retrieve("Slugs are eating my lettuce seedlings", sections)[0].title).toBe("Pests: slugs and snails");
  });

  it("returns nothing for an off-topic question and says so in the prompt", () => {
    expect(retrieve("cheapest greenhouse heater brand", sections)).toEqual([]);
    expect(buildSystemPrompt("zzz qqq", sections).system).toContain("(no relevant excerpt found)");
  });

  it("puts retrieved excerpts into the system prompt", () => {
    const { system, used } = buildSystemPrompt("How do I fix clay soil drainage?", sections);
    expect(used[0]).toBe("Soil: clay and drainage");
    expect(system).toContain("composted bark");
  });
});
