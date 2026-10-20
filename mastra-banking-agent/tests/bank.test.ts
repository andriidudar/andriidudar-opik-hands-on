import { describe, expect, it } from "vitest";
import { getBalance, listTransactions, freezeCard, type Account } from "../src/bank.ts";

const accts = (): Account[] => [
  { account_id: "CHK-1", type: "checking", currency: "USD", balance: 10, card_id: "CARD-1", card_status: "active" },
];
const txs = [
  { tx_id: "a", account_id: "CHK-1", date: "2026-01-01", merchant: "A", amount: -1, category: "x" },
  { tx_id: "b", account_id: "CHK-1", date: "2026-01-03", merchant: "B", amount: -2, category: "x" },
  { tx_id: "c", account_id: "CHK-2", date: "2026-01-02", merchant: "C", amount: -3, category: "x" },
];

describe("bank logic", () => {
  it("returns a balance and normalises the id", () => {
    expect(getBalance(" chk-1 ", accts())).toMatchObject({ balance: 10 });
  });
  it("reports unknown accounts instead of throwing", () => {
    expect(getBalance("NOPE", accts())).toHaveProperty("error");
  });
  it("lists newest transactions first and honours the limit", () => {
    const r = listTransactions("CHK-1", 1, txs, accts()) as any;
    expect(r.transactions.map((t: any) => t.tx_id)).toEqual(["b"]);
  });
  it("freezes a card once, then notes it is already frozen", () => {
    const a = accts();
    expect(freezeCard("card-1", "fraud", a)).toMatchObject({ status: "frozen", reason: "fraud" });
    expect(freezeCard("CARD-1", "fraud", a)).toHaveProperty("note");
  });
});
