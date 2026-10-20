# beeai-py-aquarium-alerts

**A ReAct agent that reads tank logs and decides whether to wake the aquarist, with every thought, tool call and token on the record in Opik.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.85-f5c518?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.105-2f54eb?style=flat)

At 12:00 a sensor in the touch pool reports an ammonia spike. Does the night aquarist get paged? A ReAct agent answers by looping: it thinks, calls a tool, reads the result, thinks again. When it pages someone for a tank that was fine, or stays quiet about one that was not, you need the loop itself, not just the verdict. This example triages alerts for a fictional public aquarium and sends the whole loop to Opik using nothing but OpenTelemetry. The agent code has no Opik calls in it.

## What you'll build

One BeeAI `ReActAgent` on `gpt-4o-mini` with three tools over fictional files in `data/`:

- `read_tank_log` returns the last sensor readings and the species living in a tank.
- `lookup_species_tolerance` returns the safe temperature, pH, ammonia and salinity ranges for one species.
- `page_aquarist` pages the on-call aquarist (it only appends to a list, so the demo stays offline) and refuses to page for `info`.

`python main.py` triages four scripted alerts (a hot reef tank, a harmless pH dip, an ammonia spike in the touch pool, a salinity probe that blinked offline). Then it does two things in Opik: it creates an `aquarium-alerts` dataset holding each alert and the severity an aquarist would assign, and it writes two feedback scores onto each alert's trace: `severity_match` (1.0 exact, 0.5 one level off) and `page_policy` (did the paging decision fit the severity).

Tracing is `aquarium/tracing.py`: an OTLP exporter aimed at Opik, plus `openinference-instrumentation-beeai`. A small exporter wrapper reshapes spans on the way out (see Gotchas).

## See it in Opik

Open the **beeai-py-aquarium-alerts** project. The Traces tab holds 4 traces named `ReAct`, one per alert, 28 spans in total. Each trace shows a `severity_match` and a `page_policy` column. In my verified run the touch-pool alert (A3) scored `severity_match` 0.5: the agent read 0.31 ppm ammonia against the sea star limit of 0.05 and answered `critical` where the dataset says `warning`. Filter on `severity_match < 1` and that trace is the only one left. Its `page_policy` is still 1.0, since paging was right either way.

Open that trace. The root is a `ReAct` span (type general) whose metadata lists every iteration: `metadata.iterations.1.thought`, `.tool_name`, `.tool_input`, `.tool_output`, up to the final answer. Its children, in order, are `OpenAIChatModel` llm spans (model `gpt-4o-mini`, provider `openai`, prompt/completion tokens, estimated cost) interleaved with `read_tank_log`, `lookup_species_tolerance` and `page_aquarist` spans of type tool, whose input and output are the exact arguments and JSON the tool saw. A3 used 4,557 tokens for about $0.00076; the whole run cost roughly $0.002 and took about 27 seconds.

There is no separate span per ReAct iteration in this instrumentation version. The iteration structure lives in the root span's metadata and in the alternation of llm and tool spans.

The Datasets tab shows `aquarium-alerts` with 4 items.

## Run it yourself

1. `cd beeai-py-aquarium-alerts`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or export it in your shell).
3. Have Opik running locally at `http://localhost:5173` (workspace `default`). For Opik Cloud, change `OPIK_OTEL_ENDPOINT` to `https://www.comet.com/opik/api/v1/private/otel`, add an `Authorization` header in `aquarium/tracing.py`, and configure the SDK with `opik configure`.
4. `uv run main.py`
5. `uv run verify.py` prints what Opik holds: trace and span counts, usage, cost and scores.

## Poke around

- Change `AQUARIUM_MODEL` to `openai:gpt-4.1-mini` and compare token counts and cost per trace.
- Add an alert about tank `reef-3` salinity to `data/alerts.json` and see which tool calls the agent chooses first.
- Edit `INSTRUCTIONS` in `aquarium/agent.py` to define "warning" more tightly and watch `severity_match` for A3 change.
- Lower `max_iterations` in `triage` and compare how the root span's iteration metadata changes.

## Gotchas we hit

**The llm span has token counts but the cost column is empty, and tools show as `general`.** OpenInference sets `llm.provider` and `llm.model_name`, but Opik takes the provider from `gen_ai.system`, so without it it cannot price the call. Tool spans only become `tool` spans when they carry `gen_ai.tool.call.arguments` / `.result`. `shape_for_opik` in `aquarium/tracing.py` copies `llm.provider` to `gen_ai.system` and the tool input/output to those attributes before export.

**A trace has hundreds of `new_token` spans.** BeeAI streams the model's answer and the instrumentation emits one span per token chunk (an early run filled my 1,000-span query limit, 974 of them tokens). They bury the real steps. Passing `stream=False` to `ReActAgent` did not help in my test: the run failed with `The generated output does not adhere to the schema`. The exporter wrapper drops spans named `new_token` instead.

**Some llm spans report 0 tokens.** In the verified run 5 of 14 llm spans carried zero usage and no cost, so trace totals under-count. The model was still called; the usage simply was not captured for those streamed responses.

**Traces land in "Default Project", or the SDK warns about it.** For OTLP, the `projectName` header is what routes spans; for the Python SDK client, pass `opik.Opik(project_name=...)` (see `main.py`).

## How it's put together

- `main.py` runs the alerts, then flushes spans and writes the dataset and scores.
- `aquarium/agent.py` has the instructions, the `ReActAgent`, and the final-answer parser.
- `aquarium/tools.py` has the three tools and the data loading.
- `aquarium/tracing.py` has the OTLP setup, the instrumentor, and the span-shaping exporter.
- `aquarium/scoring.py` has the pure scoring functions.
- `aquarium/feedback.py` creates the dataset and attaches feedback scores to traces.
- `verify.py` reads back traces, spans, usage, cost and scores.
- `data/` holds fictional tanks, species tolerances and the scripted alerts.
- `tests/` has offline tests for tools, parser, scoring, a stubbed agent run and the span shaping, including a real instrumented tool call. Run them with `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`. Tracing here is OpenTelemetry, so `OPIK_TRACK_DISABLE` is not what keeps it quiet; the tests simply use an in-memory exporter.

*built with Opik · inspired by Opik's examples and documentation*
