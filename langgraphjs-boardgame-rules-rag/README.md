# langgraphjs-boardgame-rules-rag

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![LangGraph.js](https://img.shields.io/badge/LangGraph.js-1.5-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.105-2f54eb?style=flat)

**A rules referee for three invented board games, where every wrong "the rulebooks don't say" can be traced to the chunk that was never retrieved.**

Rules questions are a nasty test for RAG. The answer is usually one sentence, buried in one section, and a model that is told to stay inside the excerpts will happily answer "the rules don't say" when retrieval simply missed. From the outside that looks like a careful, honest bot. This example builds a small referee in LangGraph.js, traces it with Opik, and scores it on a dataset so that mistake becomes a number and a trace you can click.

## What you'll build

- Three fictional rulebooks in `data/` (Tidewrack, Moth Lantern, Quillfall), split into one chunk per `##` section and embedded with `text-embedding-3-small` into an in-memory index.
- A two-node LangGraph graph: `retrieve` (a `BaseRetriever` returning the top 3 chunks) then `generate` (`gpt-4o-mini`, told to answer only from the excerpts).
- `OpikCallbackHandler` from `opik-langchain` attached to the invocation, so each question becomes a trace.
- A 10-question dataset (7 answerable, 3 the rulebooks cannot answer) and an experiment scored with the SDK's `Hallucination` metric and a `ContextPrecision` metric written here. The TypeScript SDK has no `ContextPrecision` class, so ours is a small `BaseMetric` subclass: an LLM judge says yes or no per retrieved chunk, and the score is average precision over the ranked list.

## See it in Opik

Open the **langgraphjs-boardgame-rules-rag** project. The Traces tab holds 14 traces from one run: 4 named `LangGraph` (the demo questions) and 10 named `evaluation_task` (the experiment items).

Open a `LangGraph` trace. The tree has `LangGraph` at the root, then `retrieve` (a chain span) containing a `RulesRetriever` span of type `tool` whose output is the three chunks with their game and section, then `generate` containing a `ChatOpenAI` span of type `llm` with the full prompt, the answer, token usage and estimated cost. That retriever span is what lets you tell a search failure from a prompt failure.

Then go to **Experiments** and open `rules-rag-gpt-4o-mini-k3` (10 items, linked to the dataset `boardgame-rules-questions`). In the verified run the averages were `context_precision` 0.80 and `hallucination_metric` 0.20. The rows worth reading:

- "Can I trade salvage with a player who is on a different reef tile in Tidewrack?" The answer is "The rulebooks don't say." The rule exists (Tidewrack, Turn structure: trading needs both players on the same tile), but retrieval returned Diving and salvage, Winning and Setup. Context precision is 0, and the retriever span in a trace shows exactly why. Hallucination scored it 0, because the answer is faithful to what was retrieved. That is the point: faithfulness alone cannot see this failure, the retrieval metric can.
- "What is the maximum number of players for Moth Lantern with the expansion pack?" is a legitimate abstention, yet the hallucination judge scored it 1 (it argued the context implies a maximum of 5). Treat LLM-judge scores as signals to read, not truth.
- "In Quillfall, what is a molt..." also scored 1 on hallucination, with a reason in the score's tooltip.

Experiment traces (`evaluation_task`) contain the task and the metric calls but not the graph's retrieve/generate spans; those are in the 4 `LangGraph` traces. See Gotchas.

## Run it yourself

Node 20+ and a local Opik at `http://localhost:5173`. From the repo root, put `OPENAI_API_KEY` in `.env` (or copy `.env.example` to `langgraphjs-boardgame-rules-rag/.env`).

1. `cd langgraphjs-boardgame-rules-rag`
2. `npm install`
3. `npm run demo`
4. `npm test` (offline: no keys, no Opik; use `OPIK_TRACK_DISABLE=true npm test` to be explicit)

A run takes about 12 seconds of work and costs a few cents. Running it again adds 14 more traces and a second experiment with the same name; delete the old ones first if you want clean counts (the dataset is cleared and refilled each run).

## Poke around

1. Change `k` from 3 to 1 or 5 in `src/main.ts` (and the experiment name) and compare the two experiments side by side. Does the trade question get fixed? What happens to context precision?
2. Make `chunkRulebook` split on sentences instead of sections, and see which questions break.
3. Swap the `Hallucination` judge between `gpt-4o-mini` and `gpt-4.1-mini`; watch the abstention rows change.
4. Add a fourth game to `data/` and a couple of questions to `src/questions.ts`.

## Gotchas we hit

- **Symptom:** `npm install opik-langchain` complains about a peer dependency on `opik@^1.8.75`. **Cause:** the package declares a stale peer range though it works with opik 2.x. **Fix:** pin `opik` and add to `package.json`: `"overrides": { "opik-langchain": { "opik": "2.2.105" } }`.
- **Symptom:** experiment traces show no `retrieve` or `generate` spans, only `llm_task` and metric spans. **Cause:** `evaluate()` opens its own trace per item. A second `OpikCallbackHandler` inside the task creates a separate `LangGraph` trace per item (we tried: 24 traces instead of 14) rather than nesting. **Fix:** we kept the handler for the demo questions only and read retrieval in those traces.
- **Symptom:** the hallucination column flags correct "the rulebooks don't say" answers. **Cause:** with `gpt-4o-mini` as judge, 4 of 10 items scored 1 in our first run, three of them abstentions. **Fix:** `new Hallucination({ model: "gpt-4.1-mini" })` cut that to 2 of 10 (average 0.40 to 0.20); the remaining ones are still debatable.
- **Symptom:** TypeScript rejects `new OpikCallbackHandler({ tags: ["demo"] })` (`Type 'string' is not assignable to type 'undefined'`). **Cause:** the option is typed as `[]`. **Fix:** use `metadata: { stage: "demo" }`.

## How it's put together

- `src/main.ts`: the whole run: traced questions, dataset, experiment, final flush.
- `src/graph.ts`: the `RulesRetriever` and the LangGraph `retrieve` to `generate` graph.
- `src/rules.ts`: section chunking, rulebook loading, cosine top-k.
- `src/contextPrecision.ts`: the custom `ContextPrecision` metric and average precision.
- `src/questions.ts`: the 10 dataset questions with reference answers.
- `data/*.md`: the three fictional rulebooks.
- `tests/rules.test.ts`: offline tests for chunking, ranking, the metric, and the graph with stub models and tracking disabled.
- `package.json`, `tsconfig.json`, `.env.example`, `.gitignore`: setup.

*built with Opik · inspired by Opik's examples and documentation*
