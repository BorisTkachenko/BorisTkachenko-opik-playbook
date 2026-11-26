import { streamText, convertToModelMessages, type LanguageModel, type UIMessage } from "ai";
import { OpikExporter } from "opik-vercel";
import { buildSystemPrompt } from "./garden";

export const TRACE_NAME = "garden-chat-turn";

export function lastQuestion(messages: UIMessage[]): string {
  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  return lastUser?.parts.map((p) => (p.type === "text" ? p.text : "")).join(" ") ?? "";
}

// One chat turn: retrieve guide excerpts, then stream the model's answer.
export async function startChat(model: LanguageModel, chatId: string, messages: UIMessage[]) {
  const { system } = buildSystemPrompt(lastQuestion(messages));

  return streamText({
    model,
    system,
    messages: await convertToModelMessages(messages),

    // Both settings below are the Opik hook. runtimeContext carries the chat id; the enrichSpan hook
    // in telemetry.ts turns it into the thread id, so every turn of one chat joins one Opik thread.
    // getSettings names the trace "garden-chat-turn". The reply streams to the browser untouched;
    // Opik records the trace (input messages, output, usage, cost) once the last token has arrived.
    runtimeContext: { threadId: chatId, traceName: TRACE_NAME },
    experimental_telemetry: {
      ...OpikExporter.getSettings({ name: TRACE_NAME }),
      includeRuntimeContext: { threadId: true, traceName: true },
    },
  });
}
