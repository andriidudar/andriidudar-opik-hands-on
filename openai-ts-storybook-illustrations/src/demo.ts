// Storybook illustrator: turns each page in data/pages.json into a picture
// with the OpenAI Images API, using a brief template. Output goes to ./output.
import path from "node:path";
import process from "node:process";
import OpenAI from "openai";
import { Opik } from "opik";
import { trackOpenAI } from "opik-openai";
import { illustrate } from "./illustrate.js";
import { briefVariables, loadStory } from "./pages.js";
import { BRIEF_V1, BRIEF_V2, PROMPT_NAME, render } from "./prompts.js";

delete process.env.OPENAI_BASE_URL;
for (const envFile of [".env", "../.env"]) {
  try {
    process.loadEnvFile(path.resolve(envFile));
  } catch {
    // keys may come from the environment
  }
}

const PROJECT = "openai-ts-storybook-illustrations";

// The Opik client sends traces to the local stack (OPIK_URL_OVERRIDE) and files
// them under this project; without projectName they would land in "Default Project".
const opik = new Opik({ projectName: PROJECT });

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
      const vars = briefVariables(story, page);
      const prompt = render(template, vars);
      if (dryRun) {
        console.log(`--- ${page.id} ---\n${prompt}`);
        continue;
      }

      // One trace per page: input = the page variables and rendered brief,
      // tagged with the brief version so v1 and v2 pictures can be filtered apart.
      const trace = opik.trace({
        name: "illustrate-page",
        input: { ...vars, image_prompt: prompt },
        tags: [version, page.id],
        metadata: { prompt_name: PROMPT_NAME, prompt_version: version },
      });

      // trackOpenAI wraps the client: images.generate becomes a child span of
      // the trace above, carrying the exact prompt and the usage OpenAI reports.
      const tracked = trackOpenAI(openai, {
        client: opik,
        parent: trace,
        generationName: "images.generate",
      });

      try {
        const { file, b64 } = await illustrate(tracked, prompt, path.join("output", `${version}-${page.id}.png`));
        // A base64 data URI in the trace output is what makes the PNG show up as an
        // attachment in the trace: the Opik SDK detects it and uploads the file.
        trace.update({ output: { image: `data:image/png;base64,${b64}`, file } });
        console.log(`  ${page.id} -> ${file}`);
      } finally {
        trace.end();
      }
    }
  }

  // Traces are sent in batches; flush so nothing is lost when the process exits.
  await opik.flush();
}

main().catch(async (error) => {
  console.error("Run failed:", error);
  await opik.flush();
  process.exit(1);
});
