# vercel-ai-sveltekit-garden-chat

![TypeScript](https://img.shields.io/badge/typescript-5.6%2B-3178C6?style=flat&logo=typescript&logoColor=white)
![SvelteKit](https://img.shields.io/badge/sveltekit-2-FF3E00?style=flat&logo=svelte&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
[![Opik](https://img.shields.io/badge/opik--vercel-2.2%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

**A streaming plant-care chat in SvelteKit where every reply is traced, grouped into a conversation, and graded by a judge you never call.**

A chat reply is a stream, and each request re-sends the whole history. That makes it awkward to observe: there is no single return value to log, and request logs show you a pile of near-duplicate prompts instead of what a person actually went through. Nobody is going to read every transcript to check quality either.

This example is "Sprout", a home-gardening assistant. It answers from a handful of fictional care notes (tomatoes, basil, monstera, lavender, succulents, compost, pests). The Vercel AI SDK streams the answer, one OpenTelemetry exporter ships each turn to Opik, and an online-evaluation rule in Opik grades every incoming trace on its own.

## What you'll build

- A SvelteKit page using the `Chat` class from `@ai-sdk/svelte`, and one endpoint, `src/routes/api/chat/+server.ts`, that retrieves the two best-matching notes by keyword and calls `streamText` with `gpt-4o-mini`.
- `src/lib/server/telemetry.ts`, loaded from `hooks.server.ts`: an OpenTelemetry `NodeSDK` whose exporter is `OpikExporter` from `opik-vercel`, plus the AI SDK's `registerTelemetry` integration. The chat id from the browser is passed as `threadId` so turns group into conversations.
- `scripts/rule.ts`: creates an `answer_relevance` LLM-as-judge rule on the project through Opik's REST API, only if it does not already exist.
- `npm run demo`: makes sure the rule exists, boots the dev server, plays three scripted two-turn conversations, stops the server, then polls Opik until every trace has a score.

## See it in Opik

Open the `vercel-ai-sveltekit-garden-chat` project after a demo run.

**Traces.** The table holds 12 rows: 6 named `garden-chat-turn` (one per streamed reply) and 6 named `online_evaluation`, which are the judge's own runs. Open a `garden-chat-turn` trace and you see a `step 1` span with a `chat gpt-4o-mini` span of type `llm` inside it. The input is the full message array including the system prompt with the retrieved note, so you can tell which note the model saw. In my run the second turn of the monstera conversation used 292 prompt tokens and cost $0.0000792; every turn cost between $0.00005 and $0.0001. Replies left the server as a stream, but each trace still carries the complete text and token usage.

**Threads.** The Threads tab shows 3 threads with 4 messages each (two turns, input plus output). They are the tomato, monstera and "roses, then sci-fi" conversations. The thread id is the `Chat` id the browser (or the demo script) sends.

**Scores.** Each `garden-chat-turn` trace has an `answer_relevance` feedback score (0 or 1) with the judge's reasoning, such as "The answer directly addresses the user's question about how often to water the Monstera". In the final run all 6 scored 1. In an earlier run the judge gave the sci-fi turn a 0 ("does not address the user's question") and in the later one a 1, so this judge is lenient and slightly noisy on off-topic questions. That is useful to know before you alert on it. The rule is listed under the project's Online evaluation tab.

## Run it yourself

You need Node 24 (what this was built on), an OpenAI key, and a local Opik. For the judge, the OpenAI provider key must be saved in Opik's own LLM provider settings, because the rule runs inside Opik, not in your app.

1. `cd vercel-ai-sveltekit-garden-chat && cp .env.example .env`, then add `OPENAI_API_KEY` (or keep it in a parent `.env`, which is also read).
2. `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default`
3. `npm install`
4. `npm run demo` (about 25 seconds). It prints the replies, then `6 traces, 6 scored by answer_relevance`.
5. `npm run dev` to chat yourself at the URL Vite prints. Each browser tab is its own thread.

Other scripts: `npm run rule` creates the rule if missing, `npm run clean` deletes the project's traces and leaves the rule, `npm test` runs the offline tests, `npm run check` type-checks.

## Poke around

- Run `npm run demo` again without cleaning: you get 12 chat traces, still scored, and no second rule appears in the Online evaluation tab.
- Ask Sprout something off-topic in `npm run dev` ("who won the match last night?") and watch what the judge gives it. Then edit the prompt in `scripts/opik-rest.ts`, delete the rule in the UI, and run `npm run rule`.
- Compare `prompt_tokens` across the two turns of a thread: the history is re-sent, so input grows.
- Change `gpt-4o-mini` to `gpt-4.1-mini` in the route and compare the cost column.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-vercel`.** `opik-vercel` still declares a peer dependency on opik 1.x while the current opik is 2.x. Tell npm to accept the installed version in `package.json`:

```json
"overrides": { "opik-vercel": { "opik": "$opik" } }
```

**`npm install` fails with `peer @sveltejs/kit@"^2.0.0" from @sveltejs/adapter-auto`.** SvelteKit 3 is out, but `adapter-auto` 7 only accepts 2.x. Pin `"@sveltejs/kit": "^2.70.3"`.

**The trace count is double what you sent.** Every online-rule run is logged as a trace named `online_evaluation` in the same project. Filter on `name !== "online_evaluation"` when you count your own traces (`listTraces` in `scripts/opik-rest.ts` does).

## How it's put together

- `src/routes/+page.svelte` - chat UI built on `Chat` from `@ai-sdk/svelte`.
- `src/routes/api/chat/+server.ts` - retrieval, `streamText`, and the telemetry settings with the thread id.
- `src/hooks.server.ts` - loads the telemetry module when the server starts.
- `src/lib/server/telemetry.ts` - `NodeSDK` + `OpikExporter` + `registerTelemetry`.
- `src/lib/notes.ts` - note loading, keyword retrieval, system prompt.
- `src/lib/server/env.ts` - reads `.env` files.
- `data/*.md` - the seven fictional care notes.
- `scripts/opik-rest.ts` - find-or-create the rule, list and delete traces over REST.
- `scripts/rule.ts`, `scripts/clean.ts`, `scripts/demo.ts` - the npm scripts above.
- `tests/notes.test.ts`, `tests/route.test.ts` - retrieval and prompt tests, plus a route test with a stubbed model and `OPIK_TRACK_DISABLE=true`: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true npm test`.

---

*built with Opik · inspired by Opik's examples and documentation*
