import { describe, expect, it } from "vitest";
import { ITEM_ASSERTIONS, QUESTIONS } from "../src/questions.js";
import { GLOBAL_ASSERTIONS, buildItems } from "../src/suite.js";

describe("suite items", () => {
  const items = buildItems();

  it("has one item per question, each carrying the manual as context", () => {
    expect(items).toHaveLength(QUESTIONS.length);
    for (const item of items) expect(String(item.data.context)).toContain("Owner's Manual");
  });

  it("attaches item-level assertions only where defined", () => {
    const withExtra = items.filter((i) => i.assertions);
    expect(withExtra).toHaveLength(Object.keys(ITEM_ASSERTIONS).length);
  });

  it("every item-level assertion belongs to a real question", () => {
    const questions = new Set(QUESTIONS.map((q) => q.question));
    for (const q of Object.keys(ITEM_ASSERTIONS)) expect(questions.has(q)).toBe(true);
  });

  it("has global assertions written as plain sentences", () => {
    expect(GLOBAL_ASSERTIONS.length).toBeGreaterThanOrEqual(3);
  });
});
