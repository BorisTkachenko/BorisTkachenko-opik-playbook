// Plain banking logic over the offline fictional data in data/accounts.json.
// No Opik and no Mastra in this file: it is what the unit tests exercise.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface Transaction {
  id: string;
  account_id: string;
  date: string;
  merchant: string;
  category: string;
  amount: number;
}
export interface Account { id: string; type: string; currency: string; balance: number }
export interface Card { id: string; account_id: string; network: string; last4: string; status: "active" | "frozen" }
interface Data { customer: { id: string; name: string }; accounts: Account[]; cards: Card[]; transactions: Transaction[] }

const load = (): Data =>
  JSON.parse(readFileSync(fileURLToPath(new URL("../data/accounts.json", import.meta.url)), "utf8"));

// Card status lives in memory only: freezing never touches the JSON file.
let state: Data = load();
export const resetBank = () => { state = load(); };

export function getBalance(accountId: string) {
  const a = state.accounts.find((x) => x.id === accountId.toUpperCase());
  if (!a) return { error: `No account ${accountId}`, known_accounts: state.accounts.map((x) => x.id) };
  return { account_id: a.id, type: a.type, currency: a.currency, balance: a.balance };
}

export interface TxFilter {
  account_id: string;
  category?: string;
  merchant?: string;
  min_amount?: number; // compared against the absolute amount
  since?: string; // YYYY-MM-DD, inclusive
  limit?: number;
}

export function listTransactions(f: TxFilter) {
  const id = f.account_id.toUpperCase();
  if (!state.accounts.some((a) => a.id === id)) {
    return { error: `No account ${f.account_id}`, known_accounts: state.accounts.map((x) => x.id) };
  }
  const rows = state.transactions
    .filter((t) => t.account_id === id)
    .filter((t) => !f.category || t.category === f.category.toLowerCase())
    .filter((t) => !f.merchant || t.merchant.toLowerCase().includes(f.merchant.toLowerCase()))
    .filter((t) => f.min_amount === undefined || Math.abs(t.amount) >= f.min_amount)
    .filter((t) => !f.since || t.date >= f.since)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, f.limit ?? 5);
  return { account_id: id, count: rows.length, transactions: rows };
}

export function setCardStatus(cardId: string, status: "active" | "frozen") {
  const c = state.cards.find((x) => x.id === cardId.toUpperCase() || x.last4 === cardId);
  if (!c) return { error: `No card ${cardId}`, known_cards: state.cards.map((x) => `${x.id} (…${x.last4})`) };
  const changed = c.status !== status;
  c.status = status;
  return { card_id: c.id, network: c.network, last4: c.last4, status: c.status, changed };
}
