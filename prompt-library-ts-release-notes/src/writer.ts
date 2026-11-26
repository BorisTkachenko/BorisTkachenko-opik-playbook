import OpenAI from "openai";
import { type ChangeList, formatChangeList } from "./changelogs.js";

export const MODEL = "gpt-4o-mini";

export type ChatClient = Pick<OpenAI, "chat">;

/** Ask the model to write one release note with the given system prompt. */
export async function writeReleaseNote(
  client: ChatClient,
  systemPrompt: string,
  entry: ChangeList,
): Promise<string> {
  const response = await client.chat.completions.create({
    model: MODEL,
    temperature: 0.7,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: formatChangeList(entry) },
    ],
  });
  return response.choices[0]?.message.content ?? "";
}
