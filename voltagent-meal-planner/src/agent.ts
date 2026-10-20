import { Agent } from "@voltagent/core";
import { tools } from "./tools.ts";

export const MODEL = "gpt-4o-mini";

export const mealPlanner = new Agent({
  name: "meal-planner",
  // VoltAgent's model router resolves "openai/gpt-4o-mini" to the AI SDK's OpenAI provider.
  model: `openai/${MODEL}`,
  instructions:
    "You plan weekly dinners for a household using only the pantry and recipe tools. " +
    "Never invent recipes or pantry contents: call find_recipes to pick dishes, check_pantry " +
    "for specific items, and build_shopping_list once the dishes are chosen. " +
    "Reply with the chosen dishes and the shopping list in at most 6 short lines.",
  tools,
});
