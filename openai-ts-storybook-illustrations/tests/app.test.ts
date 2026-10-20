import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { Opik, type Prompt } from "opik";
import { trackOpenAI } from "opik-openai";
import { ensureBriefVersions, type PromptLibrary } from "../src/briefs.js";
import { illustrate } from "../src/illustrate.js";
import { briefVariables, loadStory } from "../src/pages.js";
import { BRIEF_V1, BRIEF_V2, render, templateVariables } from "../src/prompts.js";

const PNG_B64 = Buffer.from("not-really-a-png").toString("base64");
const fakeImages = { images: { generate: async () => ({ data: [{ b64_json: PNG_B64 }] }) } } as never;

describe("story data and brief templates", () => {
  const story = loadStory();

  it("loads three fictional pages", () => {
    expect(story.pages.map((p) => p.id)).toEqual(["page-01", "page-02", "page-03"]);
  });

  it("every template variable is supplied by every page", () => {
    for (const template of [BRIEF_V1, BRIEF_V2]) {
      for (const page of story.pages) {
        const vars = briefVariables(story, page);
        for (const name of templateVariables(template)) expect(vars).toHaveProperty(name);
        expect(render(template, vars)).not.toMatch(/\{\{/);
      }
    }
  });

  it("v2 adds the no-text rule that v1 lacks", () => {
    expect(BRIEF_V1).not.toMatch(/Do NOT render any words/);
    expect(BRIEF_V2).toMatch(/Do NOT render any words/);
  });

  it("render fails loudly on a missing variable", () => {
    expect(() => render("Hi {{nope}}", {})).toThrow(/nope/);
  });
});

describe("illustrate", () => {
  it("writes the decoded image to disk", async () => {
    const out = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "illus-")), "x.png");
    const result = await illustrate(fakeImages, "a snail", out);
    expect(fs.readFileSync(out).toString()).toBe("not-really-a-png");
    expect(result.b64).toBe(PNG_B64);
  });

  it("still works through the Opik wrapper when tracking is disabled", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    const opik = new Opik({ projectName: "unit-test" });
    const out = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "illus-")), "y.png");
    const tracked = trackOpenAI(fakeImages as never, { client: opik });
    const result = await illustrate(tracked as never, "a snail", out);
    expect(result.file).toBe(out);
    await opik.flush();
  });
});

describe("ensureBriefVersions", () => {
  // In-memory stand-in for the prompt library.
  function stubLibrary() {
    const versions: { template: string; changeDescription: string }[] = [];
    const library = {
      getPrompt: async ({ version }: { version?: string }) => {
        const idx = Number((version ?? "v0").slice(1)) - 1;
        return versions[idx] ? ({ version, prompt: versions[idx].template } as unknown as Prompt) : null;
      },
      api: { prompts: { createPromptVersion: async (req: { version: { template: string; changeDescription: string } }) => { versions.push(req.version); } } },
    } as unknown as PromptLibrary;
    return { library, versions };
  }

  it("creates two versions once and nothing on re-runs", async () => {
    const { library, versions } = stubLibrary();
    expect((await ensureBriefVersions(library, "p")).created).toBe(2);
    expect((await ensureBriefVersions(library, "p")).created).toBe(0);
    expect((await ensureBriefVersions(library, "p")).created).toBe(0);
    expect(versions).toHaveLength(2);
    expect(versions[1].changeDescription).toMatch(/lettering/);
  });

  it("only adds v2 when v1 already exists", async () => {
    const { library, versions } = stubLibrary();
    versions.push({ template: BRIEF_V1, changeDescription: "x" });
    expect((await ensureBriefVersions(library, "p")).created).toBe(1);
    expect(versions).toHaveLength(2);
  });
});
