import { describe, expect, it } from "vitest";
import { CASES, GLOBAL_ASSERTIONS, toSuiteItems } from "../src/suite.js";

describe("suite definition", () => {
  const items = toSuiteItems("NOTES");

  it("builds one item per case, each carrying the question and the notes", () => {
    expect(items).toHaveLength(CASES.length);
    for (const item of items) expect(item.data).toMatchObject({ context: "NOTES" });
  });

  it("stores no expected answers, only assertions", () => {
    for (const item of items) expect(Object.keys(item.data).sort()).toEqual(["context", "question"]);
  });

  it("has global assertions about verbatim quotes and about saying 'I do not know'", () => {
    expect(GLOBAL_ASSERTIONS.join(" ")).toMatch(/verbatim/);
    expect(GLOBAL_ASSERTIONS.join(" ")).toMatch(/does not know/);
  });
});
