# andriidudar-opik-hands-on

**Twenty small apps you can run in an afternoon, each one wired into [Opik](https://github.com/comet-ml/opik) so you can see what your LLM code actually did.**

![Python](https://img.shields.io/badge/Python-13_examples-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-7_examples-3178C6?logo=typescript&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-2.2.105-orange)
![License](https://img.shields.io/badge/license-Apache_2.0-blue)

Reading about tracing and evaluation only gets you so far. Each folder here is a working app with fictional data,
a real failure or comparison worth looking at, and a README that tells you which project, trace, span or
experiment to open in Opik and what you should find there. Nothing depends on an external dataset or API besides
the model provider. One example runs fully offline on a local model.

## Pick something to poke at

Grouped by the Opik feature each one is built around.

### Traces, threads and feedback

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`openai-bike-workshop-chat`](openai-bike-workshop-chat) | OpenAI SDK + `track_openai` | Py | Repair-shop chats grouped into threads, cost per turn, a satisfaction score logged after each conversation |
| [`langchain-fastapi-language-tutor`](langchain-fastapi-language-tutor) | LangChain + FastAPI + `OpikTracer` | Py | A Spanish tutor whose Threads view reads like a chat transcript, not JSON |
| [`vercel-ai-sveltekit-garden-chat`](vercel-ai-sveltekit-garden-chat) | SvelteKit + Vercel AI SDK + `opik-vercel` | TS | Streamed replies as traces, one thread per chat, and an online LLM-judge rule scoring every turn |
| [`python-sdk-manual-redaction`](python-sdk-manual-redaction) | Opik Python low-level client | Py | A PII-redaction pipeline traced span by span by hand, with leak-check feedback and what's lost without a flush |

### Agents and tool calls

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`openai-agents-pet-adoption`](openai-agents-pet-adoption) | OpenAI Agents SDK | Py | A shelter front desk handing off to specialists, tool spans, and a slip the trace makes obvious |
| [`mastra-banking-agent`](mastra-banking-agent) | Mastra + OTel exporter | TS | Agent loops with real `execute_tool` spans for balances, transactions and a card freeze |
| [`voltagent-meal-planner`](voltagent-meal-planner) | VoltAgent + OTLP | TS | Pantry and recipe tools, plus the attribute mapping that makes token cost show up |
| [`beeai-py-aquarium-alerts`](beeai-py-aquarium-alerts) | BeeAI + OpenInference | Py | A ReAct agent triaging tank alerts, with LLM and tool spans and per-alert scores |
| [`langgraph-volcano-bulletin-team`](langgraph-volcano-bulletin-team) | LangGraph + `OpikTracer` | Py | One deep trace for a planner → researcher loop → writer team, with cost per agent |
| [`temporal-py-film-festival-screening`](temporal-py-film-festival-screening) | Temporal Python SDK | Py | One trace across a client and a worker process, with the failed-then-retried activity |

### Retrieval

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`langgraphjs-boardgame-rules-rag`](langgraphjs-boardgame-rules-rag) | LangGraph.js + `opik-langchain` | TS | Retrieve and generate spans, plus an experiment scored for hallucination and context precision |
| [`ollama-langchainjs-stargazing-rag`](ollama-langchainjs-stargazing-rag) | LangChain.js + local Ollama | TS | Full tracing with zero cloud calls, retrieval as a named tool span |

### Test suites, experiments and prompts

| Example | Stack | Lang | What you'll see in Opik |
|---|---|---|---|
| [`anthropic-ts-appliance-manual-qa`](anthropic-ts-appliance-manual-qa) | Anthropic TS SDK | TS | A test suite with plain-English citation assertions, pass or fail per item |
| [`pydantic-ai-calendar-extraction`](pydantic-ai-calendar-extraction) | Pydantic AI + OTel | Py | A suite built to catch invented calendar fields, failures kept |
| [`openai-vision-trading-cards`](openai-vision-trading-cards) | OpenAI vision | Py | Generated card images attached to traces and a suite that misses a smudged stat |
| [`prompt-library-museum-labels`](prompt-library-museum-labels) | Opik Python SDK | Py | Two immutable prompt versions and the same suite going from 0% to 100% |
| [`openai-ts-storybook-illustrations`](openai-ts-storybook-illustrations) | OpenAI TS SDK (`gpt-image-1`) | TS | Generated PNGs as attachments and a v1 → v2 prompt diff you can see in the pictures |
| [`dspy-claim-verification`](dspy-claim-verification) | DSPy | Py | One suite run on an uncompiled and a compiled program, 0/9 vs 8/9 |
| [`optimizer-podcast-genre-classifier`](optimizer-podcast-genre-classifier) | Opik Agent Optimizer | Py | A score curve across optimization trials and the winner saved to the prompt library |
| [`litellm-code-review-router`](litellm-code-review-router) | LiteLLM | Py | The same diffs reviewed by two models, cost and latency side by side |

## Running one

1. Start Opik. Self-hosting is a clone and one script: see the
   [self-hosting guide](https://www.comet.com/docs/opik/self-host/overview). Point the SDK at it with `opik configure`
   (or set `OPIK_URL_OVERRIDE=http://localhost:5173/api/`). Opik Cloud works too; add `OPIK_API_KEY`.
2. Copy `.env.example` to `.env` at the repo root and fill in `OPENAI_API_KEY` (and `ANTHROPIC_API_KEY` for the two
   Claude examples). Every example looks for this one file, so you only do it once.
3. `cd` into a folder and follow its README. Python examples use [uv](https://docs.astral.sh/uv/)
   (`uv sync`, then the run command); TypeScript ones use `npm install` and `npm run demo`.

Each example logs to an Opik project named after its folder, so runs never mix.

## Inside every folder

- `README.md`: the problem, what to open in Opik, numbered run steps, things to try, and the gotchas we hit
- the app itself, small enough to read in one sitting, with a short comment on every Opik touchpoint
- `data/` or `docs/`: a small fictional corpus, generated or committed, so runs are reproducible
- offline tests (`uv run pytest` / `npm test`) that pass with no API keys and tracking turned off
- `.env.example` listing exactly the variables that example reads

The git history is worth a look too. Most examples arrive as a short series of commits, starting with the plain app
and then adding Opik. Each diff shows exactly what it takes to instrument code like this.

## License

[Apache 2.0](LICENSE).

---

*Inspired by Opik's [examples](https://github.com/comet-ml/opik) and [documentation](https://www.comet.com/docs/opik/).*
