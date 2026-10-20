# voltagent-meal-planner

*A VoltAgent meal planner whose every LLM call shows up in Opik with tokens and a dollar cost.*

![Node](https://img.shields.io/badge/node-20.19%2B-339933?style=flat&logo=node.js&logoColor=white)
![VoltAgent](https://img.shields.io/badge/%40voltagent%2Fcore-2.11.0-1b1f23?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

Point an OpenTelemetry exporter at Opik and spans arrive. That does not mean they arrive useful. VoltAgent labels its spans with its own attribute names (`llm.model`, `llm.usage.prompt_tokens`) and never says which provider served the call, so Opik can show token counts at best and cannot price them. This example fixes that with a small, tested attribute-mapping layer and shows the result in the cost column.

## What you'll build

A weekly dinner planner. One VoltAgent `Agent` on `gpt-4o-mini` has three tools over fictional data in `data/`:

- `check_pantry` looks up named ingredients in `data/pantry.json`.
- `find_recipes` filters `data/recipes.json` by tag and time and ranks dishes by how little the pantry lacks.
- `build_shopping_list` merges the shortfalls of the chosen dishes, deducting pantry stock once for the whole week.

The code is split by job. `src/data.ts` holds the pure planning logic, `src/tools.ts` and `src/agent.ts` hold the VoltAgent parts, `src/telemetry/` holds everything Opik-related, and `src/demo.ts` runs three scripted requests.

## See it in Opik

Open the **voltagent-meal-planner** project (workspace `default`). The Traces tab lists three traces named `meal-planner`, one per request. In my run their estimated costs were $0.0000804, $0.0001548 and $0.00008805, with 443, 843 and 509 total tokens. A cost value in that column is the whole point: it is populated because every trace's LLM span carries a model and a provider.

Open a trace and expand it. You get an `llm:generateText` span of type `llm` with model `gpt-4o-mini`, provider `openai`, prompt/completion/total token usage and a `total_estimated_cost`, plus one `tool.execution:<name>` span of type `tool` per tool call (`find_recipes`, `check_pantry`, `build_shopping_list`). Each tool span shows the arguments the model chose as its input. In this run the three traces held 3 `llm` spans and 8 `tool` spans in total.

## Run it yourself

1. Make sure a local Opik is running at `http://localhost:5173`.
2. `cp .env.example .env` and add `OPENAI_API_KEY` (the example also reads a repo-root `.env`).
3. `npm install`
4. `npm run demo`
5. `npx tsx src/check.ts` queries Opik's REST API and exits non-zero if an LLM span has no usage or no cost.
6. `npm test` runs the offline tests. They never import the telemetry module, so nothing talks to Opik; run `env -u OPENAI_API_KEY npm test` to confirm no key is needed.

## Poke around

- Remove the `gen_ai.provider.name` line from `src/telemetry/genai-mapper.ts` and re-run: usage still lands, the cost column goes empty.
- Change `MODEL` in `src/agent.ts` to `gpt-4.1-mini` and compare the cost per token in the trace list.
- Edit `data/pantry.json` (empty the eggs) and ask request 3 again; watch `check_pantry` return `in_stock: false` in its tool span.
- Add a `claude` model branch to `providerFor` and route a request to an Anthropic model.

## Gotchas we hit

**Symptom: the trace shows token usage but `total_estimated_cost` is empty.** Cause: VoltAgent's LLM span has `llm.model` and `llm.usage.*` but no provider attribute, so Opik cannot look up a price. Fix: set the provider next to the model before export, as `src/telemetry/genai-mapper.ts` does:

```ts
attrs["gen_ai.request.model"] = model;
attrs["gen_ai.provider.name"] = "openai"; // derived from the model name
```

I reproduced this by stripping only that attribute: the span kept `prompt_tokens: 322, total_tokens: 332` and had no cost.

**Symptom: a second observability setup silently exports nothing.** Cause: importing `src/telemetry/setup.ts` constructs VoltAgent's observability, and a second `VoltAgentObservability` created afterwards did not receive spans in my test. Fix: build one instance and pass it to `new VoltAgent({ observability })`.

## How it's put together

- `data/pantry.json`, `data/recipes.json`: the fictional pantry and six recipes.
- `src/data.ts`: loading plus pantry check, recipe ranking and shopping-list merging.
- `src/tools.ts`: the three VoltAgent tools wrapping that logic.
- `src/agent.ts`: the planner agent, model and instructions.
- `src/telemetry/genai-mapper.ts`: pure VoltAgent-to-`gen_ai.*` attribute mapping, including provider.
- `src/telemetry/exporter.ts`: exporter decorator that applies the mapping before export.
- `src/telemetry/setup.ts`: OTLP exporter aimed at Opik (`projectName` and `Comet-Workspace` headers), flush on exit.
- `src/demo.ts`: the scripted runner. `src/check.ts`: the Opik verification query.
- `tests/planner.test.ts`: vitest checks for the planner logic, tools, mapping and exporter.

---

*built with Opik · inspired by Opik's examples and documentation*
