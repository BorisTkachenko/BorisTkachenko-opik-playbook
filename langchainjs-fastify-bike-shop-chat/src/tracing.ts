/**
 * Opik wiring, kept in one file: one client for the whole process, and one
 * callback handler per visitor session.
 */
import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";

export const PROJECT_NAME = "langchainjs-fastify-bike-shop-chat";

// One shared client batches every session's traces over one connection and is the
// thing we flush. projectName set here means nothing lands in "Default Project".
// The server URL and workspace come from OPIK_URL_OVERRIDE / OPIK_WORKSPACE.
export const opikClient = new Opik({ projectName: PROJECT_NAME });

const handlers = new Map<string, OpikCallbackHandler>();

/**
 * The callback handler turns each LangChain run into an Opik trace/span tree.
 * threadId = the widget's sessionId, so every turn of one visitor's chat is
 * grouped into one thread in Opik's Threads tab. Without it you get N loose traces.
 */
export function handlerFor(sessionId: string): OpikCallbackHandler {
  let handler = handlers.get(sessionId);
  if (!handler) {
    handler = new OpikCallbackHandler({ client: opikClient, threadId: sessionId });
    handlers.set(sessionId, handler);
  }
  return handler;
}

/** Send buffered traces to Opik. Traces are batched in memory: a process that exits without this loses the last ones. */
export async function flushOpik(): Promise<void> {
  await opikClient.flush();
}
