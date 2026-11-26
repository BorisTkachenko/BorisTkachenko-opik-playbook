import { describe, expect, it } from "vitest";
import { HumanMessage, AIMessage } from "@langchain/core/messages";
import { buildDocs, loadShop, retrieve } from "../src/shop.js";
import { formatFacts, retrievalQuery } from "../src/chat.js";

const docs = buildDocs(loadShop());

describe("retrieval", () => {
  it("finds the price doc for a tune-up question", () => {
    const top = retrieve(docs, "how much is a full tune-up?")[0];
    expect(top.id).toBe("service:full-tune-up");
    expect(top.text).toContain("$129");
  });

  it("maps 'open on sunday' to the hours doc", () => {
    expect(retrieve(docs, "are you open on Sundays?").map((d) => d.id)).toContain("hours");
  });

  it("returns nothing for an off-topic question", () => {
    expect(retrieve(docs, "what is the capital of France")).toEqual([]);
    expect(formatFacts([])).toContain("no matching facts");
  });

  it("carries the previous visitor message into follow-up queries", () => {
    const history = [new HumanMessage("Tell me about the E-bike service"), new AIMessage("Sure.")];
    expect(retrievalQuery("and the price?", history)).toContain("E-bike");
    expect(retrievalQuery("hello", [])).toBe("hello");
  });
});
