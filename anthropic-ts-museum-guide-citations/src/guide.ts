import Anthropic from "@anthropic-ai/sdk";
import { getTrackContext, track } from "opik";
import { PROJECT_NAME } from "./tracing.js";
import { buildSystemPrompt, loadNotes } from "./notes.js";

export const MODEL = "claude-haiku-4-5-20251001";

export const NOTES = loadNotes();
export const SYSTEM_PROMPT = buildSystemPrompt(NOTES, process.env["LAX_GUIDE"] === "1");

export const anthropic = new Anthropic();

async function callClaude(question: string): Promise<string> {
  const startTime = new Date();
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 600,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: question }],
  });
  const text = response.content.map((b) => (b.type === "text" ? b.text : "")).join("");

  // Opik has no first-party TypeScript integration for the Anthropic SDK, so the llm span is opened
  // by hand under the current `track` span. model + provider + prompt/completion tokens are what let
  // Opik price the call: leave them out and the span shows no cost.
  getTrackContext()?.span.span({
    name: "anthropic.messages.create",
    type: "llm",
    model: response.model,
    provider: "anthropic",
    input: { system_chars: SYSTEM_PROMPT.length, messages: [{ role: "user", content: question }] },
    output: { text },
    usage: {
      prompt_tokens: response.usage.input_tokens,
      completion_tokens: response.usage.output_tokens,
      total_tokens: response.usage.input_tokens + response.usage.output_tokens,
    },
    startTime,
    endTime: new Date(),
  });
  return text;
}

// track opens a trace + a general span named answer_question around each call; the llm span above
// nests inside it. Inside a suite run the same function nests under that item's evaluation trace.
export const askGuide = track({ name: "answer_question", type: "general", projectName: PROJECT_NAME }, callClaude) as (
  question: string,
) => Promise<string>;
