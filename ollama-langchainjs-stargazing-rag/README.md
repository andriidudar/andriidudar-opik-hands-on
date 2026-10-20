# ollama-langchainjs-stargazing-rag

*Ask your astronomy club's observing log questions, with a 1B model on your laptop, and still see every step in Opik.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![LangChain.js](https://img.shields.io/badge/LangChain.js-%40langchain%2Follama-1C3C3C?style=flat)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A1b-grey?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.2.105-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

Running a model locally removes the API bill and the data-sharing question, but not the debugging question. A 1B-parameter model ignores its context more readily than a hosted one, so when an answer is off you need to know whether retrieval fetched the wrong log entries or the model ignored the right ones. This example puts a small RAG app on a native Ollama server and uses Opik to answer that question. No OpenAI or Anthropic call is made anywhere, and no provider key exists in the project.

## What you'll build

A question-answering chain over the observing log of the Fernhill Astronomical Society, a fictional amateur club. Five markdown files in `docs/` hold sessions, sky-conditions guidance, equipment notes, a target cheat sheet and club rules (19 sections in total).

- Chat runs on `llama3.2:1b` and embeddings on `nomic-embed-text`, both through `@langchain/ollama` against `http://localhost:11434`.
- The vector store is LangChain's in-memory store. Nothing is persisted.
- Retrieval is wrapped as a named LangChain **tool**, `search_observing_log`, so it always shows up as its own `tool` span.
- The demo asks four questions. The fourth (drone photography) is not in the log, to check whether the model admits it.

## See it in Opik

Open the project `ollama-langchainjs-stargazing-rag`. The traces table holds four traces, all named `ask_observing_log`, one per question. Open any one and the tree reads:

- `ask_observing_log` (general), the whole chain run
  - `gather_context` (general), the step that calls retrieval
    - `search_observing_log` (tool), input is the question, output is the three log sections that matched, each labelled with its file and heading
  - `ChatPromptTemplate` (general), the assembled prompt
  - `ChatOllama` (llm), the prompt messages and the answer, with model `llama3.2:1b` and provider `ollama`
  - `StrOutputParser` (general)

For the Messier-marathon question, the tool span's output contains the 14 March section, and the answer reads "The seeing was 4/5 and the limiting magnitude was 6.4 at the zenith." For the drone question, the tool span still returns three sections (a vector store always returns its nearest neighbours) and the model answers "The log does not say.", so the span shows that the refusal came from the prompt rather than from empty retrieval.

Token usage and cost columns are empty for these runs: the LangChain-to-Ollama path does not hand Opik a token count here, so this example is about tracing, not cost.

## Run it yourself

You need Node 20+ and an Ollama server with two models: `ollama pull llama3.2:1b` and `ollama pull nomic-embed-text`. You also need an Opik server (the defaults assume self-hosted at `localhost:5173`).

1. `cd ollama-langchainjs-stargazing-rag`
2. `cp .env.example .env` (edit the Opik URL or add `OPIK_API_KEY` for Opik Cloud; no provider key needed)
3. `npm install`
4. `npm run demo`

Tests run offline against stubbed models: `OPIK_TRACK_DISABLE=true npm test`. `OPIK_TRACK_DISABLE=true` is the SDK's switch that turns the Opik client into a no-op.

## Poke around

- Add a fifth question about something that is almost in the log (for example Jupiter's visibility in spring) and compare the `search_observing_log` output with the `ChatOllama` answer.
- Change `TOP_K` in `src/config.ts` from 3 to 1 and see which questions lose the section they needed.
- Set `CHAT_MODEL=llama3.2:3b` in `.env` (after pulling it) and compare the two answers to the equipment question side by side.
- Edit the cancel-night thresholds in `docs/sky-conditions-guide.md`, re-run, and check that the answer follows the edit.

## Gotchas we hit

**The tool span has an input but an empty output.** Calling the tool as `searchTool.invoke({ query })` returns a plain string, and `OpikCallbackHandler.handleToolEnd` only records the output when it is a `ToolMessage`. Fix: invoke it with a tool call, which makes LangChain return a `ToolMessage`:

```ts
await searchTool.invoke({ type: "tool_call", id: "call_search", name: "search_observing_log", args: { query } }, config)
```

**`npm install` for `opik-langchain` warns about `opik`.** `opik-langchain@2.2.105` declares a stale peer dependency on `opik@^1.8.75`. The `overrides` block in `package.json` pins `opik` to `2.2.105` for the whole tree.

## How it's put together

- `src/config.ts`: model names, Ollama URL, Opik project and server defaults.
- `src/ingest.ts`: reads `docs/`, splits by `##` section, builds the in-memory vector store.
- `src/retriever.ts`: the `search_observing_log` tool and context formatting.
- `src/chain.ts`: prompt, the retrieval step and the `ChatOllama` pipeline.
- `src/demo.ts`: runs the four questions, one `OpikCallbackHandler` per question, then flushes.
- `docs/`: the fictional observing log.
- `tests/rag.test.ts`: six offline tests (splitting, formatting, tool, chain, prompt, handler attached with tracking disabled).

---

*built with Opik · inspired by Opik's examples and documentation*
