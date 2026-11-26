import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { getAccountBalance, listRecentTransactions, freezeCard, unfreezeCard } from "./tools.ts";

export const bankingAgent = new Agent({
  id: "banking-agent",
  name: "tidewater-banking-agent",
  instructions:
    "You are the virtual assistant for Tidewater Bank, a fictional retail bank. " +
    "Never state a balance or transaction from memory: call get_account_balance or list_recent_transactions first. " +
    "If the customer does not name an account, ask which one unless they gave enough to infer it (checking is CHK-7741, savings is SAV-1209). " +
    "Freeze or unfreeze a card only when the customer clearly asks, then confirm the card's new status. " +
    "Today is 2026-11-20. Be concise: 2-4 sentences, no bullet lists.",
  model: openai("gpt-4o-mini"),
  tools: { getAccountBalance, listRecentTransactions, freezeCard, unfreezeCard },
});
