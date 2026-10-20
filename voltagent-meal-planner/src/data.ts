// Loads the fictional pantry and recipe fixtures from data/ and holds the
// planner's pure logic, so the tools stay thin and the logic is unit-testable.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export type Ingredient = { item: string; quantity: number; unit: string };
export type Recipe = { id: string; name: string; tags: string[]; minutes: number; ingredients: Ingredient[] };

const readJson = <T>(file: string): T =>
  JSON.parse(readFileSync(fileURLToPath(new URL(`../data/${file}`, import.meta.url)), "utf8")) as T;

export const loadPantry = (): Ingredient[] => readJson<Ingredient[]>("pantry.json");
export const loadRecipes = (): Recipe[] => readJson<Recipe[]>("recipes.json");

const norm = (s: string) => s.trim().toLowerCase();

export function checkPantry(pantry: Ingredient[], items: string[]) {
  return items.map((name) => {
    const hit = pantry.find((p) => norm(p.item) === norm(name));
    return hit ? { item: hit.item, in_stock: true, quantity: hit.quantity, unit: hit.unit } : { item: name, in_stock: false, quantity: 0, unit: "" };
  });
}

/** Ingredients a recipe needs that the pantry lacks, or has too little of. */
export function missingFor(recipe: Recipe, pantry: Ingredient[]): Ingredient[] {
  return recipe.ingredients.flatMap((need) => {
    const have = pantry.find((p) => norm(p.item) === norm(need.item));
    const short = need.quantity - (have?.quantity ?? 0);
    return short > 0 ? [{ item: need.item, quantity: short, unit: need.unit }] : [];
  });
}

export function findRecipes(recipes: Recipe[], pantry: Ingredient[], opts: { tag?: string; maxMinutes?: number; maxMissing?: number }) {
  return recipes
    .filter((r) => !opts.tag || r.tags.includes(norm(opts.tag)))
    .filter((r) => opts.maxMinutes === undefined || r.minutes <= opts.maxMinutes)
    .map((r) => ({ id: r.id, name: r.name, minutes: r.minutes, tags: r.tags, missing: missingFor(r, pantry) }))
    .filter((r) => opts.maxMissing === undefined || r.missing.length <= opts.maxMissing)
    .sort((a, b) => a.missing.length - b.missing.length);
}

/** Merges the shortfalls of several recipes into one list, summing duplicates. */
export function buildShoppingList(recipes: Recipe[], pantry: Ingredient[], ids: string[]) {
  const totals = new Map<string, Ingredient>();
  // Deduct pantry stock once across the whole week, not once per recipe.
  const stock = new Map(pantry.map((p) => [norm(p.item), p.quantity]));
  for (const id of ids) {
    const recipe = recipes.find((r) => r.id === id);
    if (!recipe) throw new Error(`Unknown recipe id: ${id}`);
    for (const need of recipe.ingredients) {
      const key = norm(need.item);
      const have = stock.get(key) ?? 0;
      const used = Math.min(have, need.quantity);
      stock.set(key, have - used);
      const short = need.quantity - used;
      if (short > 0) {
        const prev = totals.get(key);
        totals.set(key, { item: need.item, unit: need.unit, quantity: (prev?.quantity ?? 0) + short });
      }
    }
  }
  return [...totals.values()].sort((a, b) => a.item.localeCompare(b.item));
}
