// Plain banking logic over the fictional JSON files in data/. No Mastra, no
// Opik: the tools in tools.ts are thin wrappers, which keeps this unit-testable.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface Account {
  account_id: string;
  type: string;
  currency: string;
  balance: number;
  card_id: string | null;
  card_status: string | null;
}
export interface Transaction {
  tx_id: string;
  account_id: string;
  date: string;
  merchant: string;
  amount: number;
  category: string;
}

const load = <T>(file: string): T =>
  JSON.parse(readFileSync(fileURLToPath(new URL(`../data/${file}`, import.meta.url)), "utf8")) as T;

// Fresh copy per process; freeze_card mutates this in-memory state only.
export const accounts: Account[] = load<{ accounts: Account[] }>("accounts.json").accounts;
export const transactions: Transaction[] = load<Transaction[]>("transactions.json");

const norm = (id: string) => id.toUpperCase().trim();

export function getBalance(accountId: string, accts: Account[] = accounts) {
  const a = accts.find((x) => x.account_id === norm(accountId));
  if (!a) return { error: `No account ${accountId}. Known accounts: ${accts.map((x) => x.account_id).join(", ")}.` };
  return { account_id: a.account_id, type: a.type, currency: a.currency, balance: a.balance };
}

export function listTransactions(
  accountId: string,
  limit = 5,
  txs: Transaction[] = transactions,
  accts: Account[] = accounts,
) {
  const id = norm(accountId);
  if (!accts.some((x) => x.account_id === id)) return { error: `No account ${accountId}.` };
  const rows = txs
    .filter((t) => t.account_id === id)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, limit);
  return { account_id: id, count: rows.length, transactions: rows };
}

export function freezeCard(cardId: string, reason: string, accts: Account[] = accounts) {
  const a = accts.find((x) => x.card_id === norm(cardId));
  if (!a) return { error: `No card ${cardId}.` };
  if (a.card_status === "frozen") return { card_id: a.card_id, status: "frozen", note: "Card was already frozen." };
  a.card_status = "frozen";
  return {
    card_id: a.card_id,
    account_id: a.account_id,
    status: "frozen",
    reason,
    next_step: "Card is frozen immediately. A replacement ships in 3-5 business days.",
  };
}
