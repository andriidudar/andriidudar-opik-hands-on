// Storybook illustrator: turns each page in data/pages.json into a picture
// with the OpenAI Images API, using a brief template. Output goes to ./output.
import path from "node:path";
import process from "node:process";
import OpenAI from "openai";
import { illustrate } from "./illustrate.js";
import { briefVariables, loadStory } from "./pages.js";
import { BRIEF_V1, BRIEF_V2, render } from "./prompts.js";

delete process.env.OPENAI_BASE_URL;
for (const envFile of [".env", "../.env"]) {
  try {
    process.loadEnvFile(path.resolve(envFile));
  } catch {
    // keys may come from the environment
  }
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");
  if (!dryRun && !process.env.OPENAI_API_KEY) {
    console.error("OPENAI_API_KEY is not set. Add it to .env and re-run.");
    process.exit(1);
  }
  const story = loadStory();
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY ?? "dry-run" });

  for (const [version, template] of [["v1", BRIEF_V1], ["v2", BRIEF_V2]] as const) {
    console.log(`\nBrief ${version}:`);
    for (const page of story.pages) {
      const prompt = render(template, briefVariables(story, page));
      if (dryRun) {
        console.log(`--- ${page.id} ---\n${prompt}`);
        continue;
      }
      const { file } = await illustrate(openai, prompt, path.join("output", `${version}-${page.id}.png`));
      console.log(`  ${page.id} -> ${file}`);
    }
  }
}

main().catch((error) => {
  console.error("Run failed:", error);
  process.exit(1);
});
