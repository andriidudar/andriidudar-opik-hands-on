import { describe, expect, it } from "vitest";
import path from "node:path";
import { buildSystemPrompt, loadNotes, retrieve } from "../src/lib/notes";

const notes = loadNotes(path.resolve(__dirname, "../data"));

describe("garden notes", () => {
  it("loads every note with a title", () => {
    expect(notes.length).toBeGreaterThanOrEqual(7);
    expect(notes.find((n) => n.slug === "basil")?.title).toMatch(/Basil/);
  });

  it("retrieves the plant named in the question first", () => {
    expect(retrieve(notes, "Why are my basil leaves turning black?")[0].slug).toBe("basil");
    expect(retrieve(notes, "How often should I water my monstera?")[0].slug).toBe("monstera");
  });

  it("returns nothing for an off-topic question", () => {
    expect(retrieve(notes, "Who won the football match yesterday?")).toEqual([]);
  });

  it("puts retrieved notes into the system prompt", () => {
    const prompt = buildSystemPrompt(retrieve(notes, "lavender pruning"));
    expect(prompt).toContain("Lavandula");
    expect(buildSystemPrompt([])).toContain("(no matching notes)");
  });
});
