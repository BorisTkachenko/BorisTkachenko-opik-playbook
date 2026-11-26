/**
 * The chat brain: a string-in, string-out LangChain chain.
 *
 *   visitor message (string)
 *     -> load-session-history  -> lookup_shop_info (tool) -> prompt -> model -> parser
 *     -> reply (string)
 */
import { z } from "zod";
import { tool } from "@langchain/core/tools";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import type { Runnable, RunnableConfig } from "@langchain/core/runnables";
import { AIMessage, HumanMessage } from "@langchain/core/messages";
import type { BaseMessage } from "@langchain/core/messages";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

import { buildDocs, loadShop, retrieve } from "./shop.js";
import type { Doc } from "./shop.js";

export const SYSTEM_PROMPT = `You are the website chat assistant for Crankshaft Cycles,
a small bicycle repair shop. Keep replies short (2-4 sentences): this is a chat widget.

Answer ONLY from the shop facts below. Quote prices and hours exactly as written.
If the facts do not cover the question, say you are not sure and give the shop phone number.
You cannot book anything yourself: when a visitor wants a booking, suggest open slots
from the facts and tell them to phone or visit the counter to confirm.

Shop facts:
{facts}`;

export interface Session {
  history: BaseMessage[];
}

export class SessionStore {
  private sessions = new Map<string, Session>();
  get(id: string): Session {
    let s = this.sessions.get(id);
    if (!s) this.sessions.set(id, (s = { history: [] }));
    return s;
  }
  has(id: string): boolean {
    return this.sessions.has(id);
  }
}

/** Build the retrieval query: the new message plus the visitor's previous one, so "how much is that?" still works. */
export function retrievalQuery(message: string, history: BaseMessage[]): string {
  const lastHuman = [...history].reverse().find((m) => m instanceof HumanMessage);
  return lastHuman ? `${lastHuman.content as string} ${message}` : message;
}

export function formatFacts(docs: Doc[]): string {
  return docs.length ? docs.map((d) => `- ${d.text}`).join("\n") : "- (no matching facts found)";
}

export function createChat(model: BaseChatModel, sessions: SessionStore) {
  const docs = buildDocs(loadShop());

  // Retrieval lives in a named tool function, not a bare retriever, so it is a
  // first-class step with a readable name and input/output.
  const lookupShopInfo = tool(
    async ({ query }: { query: string }) => formatFacts(retrieve(docs, query)),
    {
      name: "lookup_shop_info",
      description: "Look up shop services, prices, opening hours, policies and open booking slots.",
      schema: z.object({ query: z.string() }),
    }
  );

  const loadSessionHistory = RunnableLambda.from((message: string, config?: RunnableConfig) => {
    const sessionId = (config?.configurable as { sessionId?: string } | undefined)?.sessionId;
    if (!sessionId) throw new Error("sessionId missing from config");
    return { history: sessions.get(sessionId).history, message };
  }).withConfig({ runName: "load-session-history" });

  const retrieveFacts = RunnableLambda.from(
    async (input: { history: BaseMessage[]; message: string }, config?: RunnableConfig) => ({
      ...input,
      // Passing `config` on makes the tool a child run of this chain turn.
      facts: await lookupShopInfo.invoke({ query: retrievalQuery(input.message, input.history) }, config),
    })
  ).withConfig({ runName: "retrieve-facts" });

  const prompt = ChatPromptTemplate.fromMessages([
    ["system", SYSTEM_PROMPT],
    new MessagesPlaceholder("history"),
    ["human", "{message}"],
  ]);

  const chain: Runnable<string, string> = RunnableSequence.from([
    loadSessionHistory,
    retrieveFacts,
    prompt,
    model,
    new StringOutputParser(),
  ]);

  /** One visitor turn: message in, reply out, history updated. `extra` carries callbacks, etc. */
  return async function answer(sessionId: string, message: string, extra: RunnableConfig = {}): Promise<string> {
    const reply = await chain.invoke(message, {
      ...extra,
      runName: "bike-shop-turn",
      configurable: { sessionId },
    });
    sessions.get(sessionId).history.push(new HumanMessage(message), new AIMessage(reply));
    return reply;
  };
}
