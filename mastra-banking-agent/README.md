# mastra-banking-agent

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6) ![Mastra](https://img.shields.io/badge/Mastra-1.78-black) ![Opik](https://img.shields.io/badge/traced%20with-Opik-5b8def)

A tool-calling banking assistant for a fictional bank, built on Mastra, whose every agent loop shows up in Opik as a readable tree.

## Why bother

An agent that calls tools is a loop: the model asks for a tool, the tool runs, the model reads the result, maybe asks for another. When a customer hears "your card is frozen", you want to know which tool call actually did that, with which arguments, and what the model paid to get there. A flat list of LLM calls can't tell you. A tree with real tool spans can.

## What you'll build

A personal-banking assistant for the invented "Fernbank Demo Bank". It has three tools over JSON files in `data/`:

- `get_balance` reads an account balance.
- `list_transactions` returns recent activity, newest first.
- `freeze_card` freezes a debit card (in memory only).

A demo script sends three customer messages: a two-account balance question, a transaction review that spots two identical $249 charges, and a fraud report that ends in a card freeze. Mastra's observability layer plus its OpenTelemetry exporter send each run to a local Opik.

## See it in Opik

Open http://localhost:5173, workspace `default`, project **mastra-banking-agent**.

- The Traces tab holds 3 traces named `invoke_agent fernbank-assistant`. Each one has two `llm` spans named `chat gpt-4o-mini` (the model's tool-calling step and its final answer) and one or two `tool` spans named `execute_tool ...`.
- Open the fraud trace and click its tool span. The input shows `gen_ai.tool.call.arguments` (`card_id: CARD-5523`, and the reason the model wrote), and the output shows `gen_ai.tool.call.result` with `status: frozen`.
- Click an `llm` span. Model is `gpt-4o-mini-2024-07-18`, provider `openai`, with prompt and completion tokens (for example 479 + 57 on the first step of the freeze request) and an estimated cost of about $0.0001. The trace row rolls these up: 957 tokens and $0.00018 for the freeze request.
- The Spans tab filtered by type `tool` is a quick audit of every action the agent took, with its arguments.
- Mastra also exports its internal bookkeeping (`agent_step`, `model_chunk`, `processor_run`, ...) as `general` spans, so a trace has 14 to 17 spans, most of them noise.

The trace's own Output column is empty (see Gotchas).

## Run it yourself

Needs Node 22.13+, a local Opik on `http://localhost:5173`, and an `OPENAI_API_KEY`.

1. `cd mastra-banking-agent && npm install`
2. Put `OPENAI_API_KEY` in `.env` (see `.env.example`), or in a `.env` further up the tree. `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default` go there too.
3. `npm run demo` (about 10 seconds, well under a cent)
4. `npm run check` prints each trace from Opik's REST API: span counts, tool arguments and results, tokens and cost per llm span.
5. `npm test` runs the offline tests.

## Poke around

- Ask something that needs no tool ("what can you do?") and compare: one `llm` span, no `tool` spans.
- Request a balance for a made-up account. The tool returns an `error` object; find it in the tool span's output and see how the model words it.
- Swap `MODEL` in `src/agent.ts` for `openai/gpt-4.1-mini` and watch the cost column change.
- Add `OPIK_TRACK_DISABLE=true` to the run and confirm the project gets no new traces.

## Gotchas we hit

**The trace Output column is empty.** The OTLP mapping fills the root span's input with the raw Mastra attributes (the question sits under `mastra.agent_run.input`) and never sets a trace output. The final answer is still in the last `llm` span's output. There is no mapper hook in the exporter, so read the answer from there.

**Traces land in "Default Project".** Opik's OTLP endpoint picks the project from a `projectName` header, not from the OTel `serviceName`. `src/mastra.ts` sets `headers: { projectName: "mastra-banking-agent", "Comet-Workspace": "default" }` on the exporter. Against a local Opik, do not send an `Authorization` header.

## How it's put together

- `data/accounts.json`, `data/transactions.json`: the fictional customer, accounts and transactions.
- `src/bank.ts`: plain functions behind the tools (balance, listing, freezing).
- `src/tools.ts`: the three Mastra tools, thin wrappers over `bank.ts`.
- `src/agent.ts`: the agent, its instructions and model.
- `src/mastra.ts`: the Mastra instance and the Opik OTLP exporter; `OPIK_TRACK_DISABLE=true` turns the exporter off.
- `src/demo.ts`: three scripted requests, then `mastra.shutdown()` to flush spans.
- `src/check.ts`: reads the project back from Opik and prints the trees.
- `tests/bank.test.ts`, `tests/tools.test.ts`: offline tests for the bank logic, tool execution with tracking disabled, and the exporter headers. Run them with `OPIK_TRACK_DISABLE=true npm test` and no provider keys.

*built with Opik · inspired by Opik's examples and documentation*
