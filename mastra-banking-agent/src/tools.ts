// The three tools the agent can call. Mastra runs each execute() inside an
// agent loop, so every call is a separate step with real arguments and results.
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { getBalance, listTransactions, freezeCard } from "./bank.ts";

export const getBalanceTool = createTool({
  id: "get_balance",
  description: "Get the current balance of one account (ids look like CHK-2210 or SAV-7731).",
  inputSchema: z.object({ account_id: z.string().describe("Account id, like CHK-2210") }),
  execute: async ({ account_id }) => getBalance(account_id),
});

export const listTransactionsTool = createTool({
  id: "list_transactions",
  description: "List the most recent transactions of one account, newest first.",
  inputSchema: z.object({
    account_id: z.string().describe("Account id, like CHK-9054"),
    limit: z.number().int().min(1).max(10).default(5).describe("How many transactions to return"),
  }),
  execute: async ({ account_id, limit }) => listTransactions(account_id, limit),
});

export const freezeCardTool = createTool({
  id: "freeze_card",
  description:
    "Freeze a debit card immediately. Only call this when the customer explicitly asks to freeze " +
    "the card or reports it lost, stolen or used fraudulently.",
  inputSchema: z.object({
    card_id: z.string().describe("Card id, like CARD-5523"),
    reason: z.string().describe("Why the card is being frozen"),
  }),
  execute: async ({ card_id, reason }) => freezeCard(card_id, reason),
});
