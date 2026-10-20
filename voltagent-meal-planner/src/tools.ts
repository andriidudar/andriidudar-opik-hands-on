// The planner's three tools. They only read the fixtures in data/, so the LLM
// call is the single thing that leaves your machine.
import { createTool } from "@voltagent/core";
import { z } from "zod";
import { buildShoppingList, checkPantry, findRecipes, loadPantry, loadRecipes } from "./data.ts";

export const checkPantryTool = createTool({
  name: "check_pantry",
  description: "Look up how much of each named ingredient is in the pantry.",
  parameters: z.object({ items: z.array(z.string()).min(1).describe("Ingredient names, e.g. ['eggs', 'rice']") }),
  execute: async ({ items }) => ({ results: checkPantry(loadPantry(), items) }),
});

export const findRecipesTool = createTool({
  name: "find_recipes",
  description: "Find recipes, ranked by how few ingredients the pantry is missing. Each result lists what is missing.",
  parameters: z.object({
    tag: z.string().optional().describe("Dietary or style tag: vegan, vegetarian, quick, budget, weeknight, classic"),
    max_minutes: z.number().optional().describe("Maximum total cooking time"),
    max_missing: z.number().optional().describe("Maximum number of missing ingredients"),
  }),
  execute: async ({ tag, max_minutes, max_missing }) => ({
    recipes: findRecipes(loadRecipes(), loadPantry(), { tag, maxMinutes: max_minutes, maxMissing: max_missing }),
  }),
});

export const buildShoppingListTool = createTool({
  name: "build_shopping_list",
  description: "Combine the shortfalls of the chosen recipes into one shopping list, deducting pantry stock once for the whole week.",
  parameters: z.object({ recipe_ids: z.array(z.string()).min(1).describe("Recipe ids such as ['R1', 'R2']") }),
  execute: async ({ recipe_ids }) => ({ shopping_list: buildShoppingList(loadRecipes(), loadPantry(), recipe_ids) }),
});

export const tools = [checkPantryTool, findRecipesTool, buildShoppingListTool];
