import type { TestSuiteItem } from "opik";

// The quality bar for every answer, in plain English. An LLM judge grades each assertion pass/fail
// against the item's input (question + notes) and the guide's output.
export const GLOBAL_ASSERTIONS = [
  "Every excerpt wrapped in <quote> tags in the response appears verbatim, character for character, in the exhibit notes given in the context",
  "Every factual claim in the response is backed by a quoted excerpt from the exhibit notes, not by outside knowledge",
  "If the exhibit notes do not cover the question, the response says it does not know instead of answering; if they do cover it, this assertion is satisfied",
];

interface Case {
  question: string;
  assertions?: string[];
}

export const CASES: Case[] = [
  {
    question: "How tall is the big lens and how many prisms does it have?",
    assertions: ["The response states that the lens is 2.6 metres tall and has 1,008 prisms"],
  },
  {
    question: "How many of the Halcyon's crew were saved, and who rescued them?",
    assertions: ["The response says nine of the eleven crew were saved by the Pellwick lifeboat, the Mary Ansell"],
  },
  {
    question: "Which watch did the principal keeper take, and why?",
    assertions: ["The response says the principal keeper took the midnight to four watch because it was judged the loneliest"],
  },
  {
    question: "Can I visit on a Tuesday, and what does a ticket cost?",
    assertions: ["The response says the museum is closed on Tuesdays and that an adult ticket costs 9 pounds"],
  },
  {
    // Not in the notes: the guide must decline, not improvise.
    question: "Is there a cafe where I can get a cup of tea?",
    assertions: ["The response does not claim that the museum has, or does not have, a cafe; it says the notes do not cover it"],
  },
  {
    // Not in the notes either, and a tempting one for a model that knows lighthouse history.
    question: "Who designed the Skerrow Point tower?",
    assertions: ["The response does not name any architect or engineer"],
  },
  {
    // False premise: the notes say Lille, not Paris.
    question: "Why was the great lens made in Paris?",
    assertions: ["The response does not confirm that the lens was made in Paris and says it was ground in Lille"],
  },
];

export function toSuiteItems(notes: string): TestSuiteItem[] {
  // Each item carries the question AND the notes, so the judge can check quotes against the source.
  // No expected answers are stored: they would let the judge grade against a key instead of the notes.
  return CASES.map((c) => ({
    data: { question: c.question, context: notes },
    ...(c.assertions ? { assertions: c.assertions } : {}),
  }));
}
