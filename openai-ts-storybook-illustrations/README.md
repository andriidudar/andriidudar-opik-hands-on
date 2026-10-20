# openai-ts-storybook-illustrations

*A picture-book illustrator whose prompt lives in Opik, and whose pictures show up on the traces that made them.*

![Node](https://img.shields.io/badge/node-20.12%2B-5FA04E?style=flat&logo=node.js&logoColor=white)
![openai](https://img.shields.io/badge/openai-6.x-412991?style=flat)
![opik](https://img.shields.io/badge/opik-2.2.105-2f54eb?style=flat)

You ask an image model to illustrate a page of a children's book, and it paints the page's sentence into the picture, except the sentence comes out as "Every sarning, My, sharked the eII shaver". Nothing in your logs tells you that. The prompt is a string in the code, the image is a file on disk, and when someone tweaks the wording a week later nobody can say which wording produced which picture.

This example is a small illustrator for a fictional book, *Pip and the Borrowed Moon*, about a snail who lights garden lanterns. It keeps the "illustration brief" in the Opik prompt library, versions it, and attaches every generated PNG to its trace.

## What you'll build

- `data/pages.json`: three story pages, each with the text, a setting, and a mood.
- A brief template, `storybook-illustration-brief`, registered in the Opik prompt library as two versions. **v1** just describes the book, the hero, the scene, the page text and the mood. **v2** adds house-style rules: no rendered words, one watercolor look, calm space at the bottom for text.
- A runner that fetches both versions from the library, fills them in for each page, and calls `gpt-image-1` (quality `low`, 1024x1024) through an OpenAI client wrapped with `opik-openai`. That is 3 pages x 2 versions = 6 images, a few cents in total.
- One `illustrate-page` trace per image, tagged with the page and the brief version, with the PNG attached.

## See it in Opik

Open the **openai-ts-storybook-illustrations** project. The Traces tab lists 6 `illustrate-page` traces, tagged `v1` or `v2` plus `page-01` to `page-03`. Click one: the input holds the page variables and the exact brief that was sent, the metadata pins `prompt_name`, `prompt_version` and `prompt_id`, and the trace carries one attachment, a PNG of about 1.3 to 1.7 MB, which renders as the picture. Inside the trace sits one `images.generate` span for `gpt-image-1` with 388 tokens (v1) or about 487 (v2, the longer brief) and an estimated cost of roughly $0.0006 and $0.001. Filter on the `v1` tag, open the three attachments, and you see the problem: every one has garbled lettering where the story text leaked into the picture. Filter on `v2` and none of the three has any (in our run).

Then open **Prompts** and pick `storybook-illustration-brief`. It has 2 versions. The version history shows the change reason on v2: *"Add house-style rules: the story text was being drawn into the pictures as garbled lettering..."*, and the compare view highlights the added "House style rules" block against v1. The trace's `prompt_version` links each picture to the version that made it.

## Run it yourself

1. `cd openai-ts-storybook-illustrations`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or rely on a repo-root `.env`). For local Opik also set `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`.
3. `npm install`
4. `npm run demo` (about 70 seconds; `npm run demo -- --dry-run` prints the rendered briefs without calling OpenAI or Opik).
5. Look at the project, the attachments and the prompt as described above. The PNGs are also in `output/` (git-ignored).

Re-running is safe for the prompt library: the setup looks each version up first, so it never goes past 2 versions. Each run adds 6 new traces.

## Poke around

- Add a v3 to `src/prompts.ts` and `src/briefs.ts` ("each page must show the same leaf pattern on the shell") and compare the attachments per `prompt_version`.
- Remove the "Do NOT render any words" line from a copy of v2 and see whether the lettering comes back.
- Change `IMAGE_QUALITY` to `"medium"` in `src/illustrate.ts` and compare the image tokens and cost on the span.
- Edit `data/pages.json` with your own story; nothing else needs to change.

## Gotchas we hit

**The prompt version has no change reason in the history.** We passed `changeDescription` to `opik.createPrompt` (opik 2.2.105) and the prompt had both versions, but the REST response for each version had no `change_description` at all. The SDK's `createPrompt` does not forward that field to the version it creates. Call the API client directly instead:

```ts
await opik.api.prompts.createPromptVersion({
  name, projectName,
  version: { template, type: PromptType.MUSTACHE, changeDescription, tags },
});
```

**The `images.generate` span is `general`, not `llm`.** The span has the model, token usage and an estimated cost, but its type is `general`. Don't filter on span type `llm` to find your image calls; filter on the span name, `images.generate`.

## How it's put together

- `src/demo.ts`: the run: prompt setup, one trace per image, flush.
- `src/briefs.ts`: find-or-create of the two brief versions in the prompt library.
- `src/prompts.ts`: the v1 and v2 templates, the change reasons, a small renderer for `--dry-run` and tests.
- `src/illustrate.ts`: the `gpt-image-1` call and saving the PNG.
- `src/pages.ts`: loads `data/pages.json` and builds the template variables.
- `data/pages.json`: the fictional story.
- `tests/app.test.ts`: offline vitest checks (templates, find-or-create with a stubbed library, the image call, and the traced client with tracking disabled).

Run the tests with `npm test`. They need no keys; set `OPIK_TRACK_DISABLE=true` to turn Opik tracking off (the README run above leaves it on).

*built with Opik · inspired by Opik's examples and documentation*
