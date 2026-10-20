import { Agent } from "@mastra/core/agent";
import { getBalanceTool, listTransactionsTool, freezeCardTool } from "./tools.ts";

export const MODEL = "openai/gpt-4o-mini";

export const bankingAgent = new Agent({
  id: "banking-agent",
  name: "fernbank-assistant",
  instructions:
    "You are the personal-banking assistant for Fernbank Demo Bank, a fictional bank. " +
    "The customer has accounts CHK-2210, SAV-7731 and CHK-9054; cards are CARD-4417 (on CHK-2210) and CARD-5523 (on CHK-9054). " +
    "Ground every answer in tool results; never guess balances or transactions. " +
    "Call get_balance for balances and list_transactions for activity. " +
    "Only call freeze_card when the customer clearly asks for it or reports fraud. " +
    "Be concise: 2-4 sentences, no bullet lists.",
  model: MODEL,
  // The object key, not the tool id, becomes the execute_tool span name in Opik,
  // so use the snake_case ids the model sees.
  tools: { get_balance: getBalanceTool, list_transactions: listTransactionsTool, freeze_card: freezeCardTool },
});
