import Anthropic from "@anthropic-ai/sdk";
import { buildSystemPrompt, loadNotes } from "./notes.js";

export const MODEL = "claude-haiku-4-5-20251001";

export const NOTES = loadNotes();
export const SYSTEM_PROMPT = buildSystemPrompt(NOTES);

export const anthropic = new Anthropic();

export async function askGuide(question: string): Promise<string> {
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 600,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: question }],
  });
  return response.content.map((b) => (b.type === "text" ? b.text : "")).join("");
}
