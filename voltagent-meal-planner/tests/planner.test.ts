import { describe, expect, it } from "vitest";
import { buildShoppingList, checkPantry, findRecipes, loadPantry, loadRecipes } from "../src/data.ts";
import { mapVoltAgentAttributes, providerFor } from "../src/telemetry/genai-mapper.ts";
import { GenAIMappingExporter } from "../src/telemetry/exporter.ts";
import { checkPantryTool } from "../src/tools.ts";

const pantry = loadPantry();
const recipes = loadRecipes();

describe("planner logic", () => {
  it("reports pantry stock and absence", () => {
    const [eggs, saffron] = checkPantry(pantry, ["Eggs", "saffron"]);
    expect(eggs).toMatchObject({ in_stock: true, quantity: 4 });
    expect(saffron.in_stock).toBe(false);
  });

  it("ranks recipes by fewest missing ingredients", () => {
    const found = findRecipes(recipes, pantry, { tag: "vegan" });
    expect(found.every((r) => r.tags.includes("vegan"))).toBe(true);
    expect(found[0].missing.length).toBeLessThanOrEqual(found[1].missing.length);
  });

  it("deducts pantry stock once across the whole week", () => {
    // R1 and R5 both need 200 g spaghetti; the pantry has 500 g, so nothing is short.
    const list = buildShoppingList(recipes, pantry, ["R1", "R5"]);
    expect(list.find((i) => i.item === "spaghetti")).toBeUndefined();
    expect(list.map((i) => i.item)).toEqual(["basil", "guanciale"]);
  });

  it("rejects unknown recipe ids", () => {
    expect(() => buildShoppingList(recipes, pantry, ["R99"])).toThrow(/Unknown recipe/);
  });
});

describe("telemetry mapping", () => {
  it("maps llm spans to gen_ai.* with provider so cost can be computed", () => {
    const attrs: Record<string, unknown> = { "span.type": "llm", "llm.model": "gpt-4o-mini", "llm.usage.prompt_tokens": 10, "llm.usage.completion_tokens": 5, "llm.usage.total_tokens": 15 };
    mapVoltAgentAttributes(attrs);
    expect(attrs).toMatchObject({ "gen_ai.request.model": "gpt-4o-mini", "gen_ai.provider.name": "openai", "gen_ai.usage.total_tokens": 15 });
  });

  it("moves tool input to gen_ai.tool.call.arguments", () => {
    const attrs: Record<string, unknown> = { "span.type": "tool", input: '{"items":["eggs"]}', "tool.parameters": "{}" };
    mapVoltAgentAttributes(attrs);
    expect(attrs["gen_ai.tool.call.arguments"]).toBe('{"items":["eggs"]}');
    expect(attrs.input).toBeUndefined();
  });

  it("knows providers by model prefix", () => {
    expect(providerFor("claude-haiku-4-5")).toBe("anthropic");
    expect(providerFor("mystery-model")).toBeUndefined();
  });
});

describe("tools", () => {
  // The telemetry module is never imported here, so no exporter exists and nothing talks to Opik.
  it("run offline against the fixtures", async () => {
    const out = await checkPantryTool.execute!({ items: ["rice"] } as never, {} as never);
    expect(out).toEqual({ results: [{ item: "rice", in_stock: true, quantity: 800, unit: "g" }] });
  });
});

describe("exporter wrapper", () => {
  it("renames attributes and forwards spans to the inner exporter", () => {
    const seen: unknown[] = [];
    const inner = { export: (spans: unknown[], done: (r: unknown) => void) => { seen.push(...spans); done({ code: 0 }); }, shutdown: async () => {} };
    const span = { attributes: { "span.type": "llm", "llm.model": "gpt-4o-mini" } };
    new GenAIMappingExporter(inner as never).export([span] as never, () => {});
    expect(seen).toHaveLength(1);
    expect(span.attributes).toHaveProperty("gen_ai.provider.name", "openai");
  });
});
