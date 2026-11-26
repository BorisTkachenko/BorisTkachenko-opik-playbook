import { beforeEach, describe, expect, it } from "vitest";
import { getBalance, listTransactions, resetBank, setCardStatus } from "../src/bank.ts";
import { freezeCard, getAccountBalance } from "../src/tools.ts";

beforeEach(resetBank);

describe("bank logic", () => {
  it("returns a balance and rejects unknown accounts", () => {
    expect(getBalance("chk-7741")).toMatchObject({ balance: 2314.58 });
    expect(getBalance("XXX")).toHaveProperty("error");
  });

  it("filters transactions by category, amount and date, newest first", () => {
    const r = listTransactions({ account_id: "CHK-7741", category: "dining", since: "2026-11-08" }) as any;
    expect(r.transactions.map((t: any) => t.id)).toEqual(["T-007"]);
    const big = listTransactions({ account_id: "CHK-7741", min_amount: 100, limit: 10 }) as any;
    expect(big.transactions.map((t: any) => t.id)).toEqual(["T-008", "T-006", "T-003", "T-002"]);
  });

  it("freezes in memory only and is idempotent", () => {
    expect(setCardStatus("4417", "frozen")).toMatchObject({ status: "frozen", changed: true });
    expect(setCardStatus("CARD-4417", "frozen")).toMatchObject({ changed: false });
    resetBank();
    expect(setCardStatus("CARD-4417", "active")).toMatchObject({ changed: false });
  });
});

describe("mastra tools (tracking off)", () => {
  it("run directly, no Opik or model involved", async () => {
    const bal = await (getAccountBalance as any).execute({ account_id: "SAV-1209" });
    expect(bal.balance).toBe(12840);
    const f = await (freezeCard as any).execute({ card: "9082" });
    expect(f.status).toBe("frozen");
  });
});
