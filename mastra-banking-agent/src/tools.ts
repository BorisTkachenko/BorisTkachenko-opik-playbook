// Mastra tool wrappers around bank.ts. Mastra runs each one inside an
// execute_tool span, so the tool's input args and output JSON are recorded.
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { getBalance, listTransactions, setCardStatus } from "./bank.ts";

export const getAccountBalance = createTool({
  id: "get_account_balance",
  description: "Get the current balance of one account (e.g. CHK-7741 or SAV-1209).",
  inputSchema: z.object({ account_id: z.string() }),
  execute: async ({ account_id }) => getBalance(account_id),
});

export const listRecentTransactions = createTool({
  id: "list_recent_transactions",
  description:
    "List recent transactions for one account, newest first, with optional filters: category, merchant substring, minimum absolute amount, start date (YYYY-MM-DD), and a limit.",
  inputSchema: z.object({
    account_id: z.string(),
    category: z.string().optional(),
    merchant: z.string().optional(),
    min_amount: z.number().optional(),
    since: z.string().optional(),
    limit: z.number().int().min(1).max(20).optional(),
  }),
  execute: async (input) => listTransactions(input),
});

export const freezeCard = createTool({
  id: "freeze_card",
  description: "Freeze a debit/credit card so it cannot be used. Takes a card id (CARD-4417) or its last four digits.",
  inputSchema: z.object({ card: z.string() }),
  execute: async ({ card }) => setCardStatus(card, "frozen"),
});

export const unfreezeCard = createTool({
  id: "unfreeze_card",
  description: "Unfreeze a previously frozen card. Takes a card id or its last four digits.",
  inputSchema: z.object({ card: z.string() }),
  execute: async ({ card }) => setCardStatus(card, "active"),
});
