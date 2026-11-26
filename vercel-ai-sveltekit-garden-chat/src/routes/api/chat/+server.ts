import { openai } from "@ai-sdk/openai";
import type { UIMessage } from "ai";
import { startChat } from "../../../lib/server/chat";
import type { RequestHandler } from "./$types";

export const POST: RequestHandler = async ({ request }) => {
  // The Chat class posts the chat id and the full message history on every turn.
  const { id, messages }: { id: string; messages: UIMessage[] } = await request.json();
  const result = await startChat(openai("gpt-4o-mini"), id, messages);
  return result.toUIMessageStreamResponse();
};
