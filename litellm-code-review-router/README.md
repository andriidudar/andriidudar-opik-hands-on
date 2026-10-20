# litellm-code-review-router

*Five tiny diffs, two models, one table: which reviewer is cheaper, and by how much?*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.35-2f54eb?style=flat)

Picking a model for an automated code-review bot usually comes down to a gut feeling. A cheap model summarizes a ten-line diff just fine, so why pay more? The honest way to decide is to send identical diffs to each candidate and look at cost and latency side by side. This example does that with LiteLLM as the router and Opik as the record. Every review is traced and labelled with the model that produced it, so the per-model comparison is a filter in the Opik UI. The script also reads the numbers back from Opik and prints the same table in your terminal.

## What you'll build

A small Python package, `review_router`, with a CLI:

- It loads five fictional diffs from `data/` (a null guard, a retry loop, an SQL string concatenation, a config rename, a cache TTL).
- It sends each one to `gpt-4o-mini` and `claude-haiku-4-5` through `litellm.completion`. The model is just a string; the prompt asks for a three-line review (Summary, Risk, Suggestion).
- Each review runs inside an `@opik.track` function, so every call becomes one trace. LiteLLM's `OpikLogger` adds an `llm` span under it with token usage and estimated cost.
- Each trace is tagged and given `metadata.model`, which is what you compare on.
- At the end the CLI prints two tables: one from the LiteLLM responses, one queried back from Opik. They should match.

## See it in Opik

Open the `litellm-code-review-router` project. In my verified run the Traces tab held 10 traces named `review_diff`, one per (model, diff) pair, each with a single child `llm` span. The tag column shows `gpt-4o-mini` on five rows and `claude-haiku-4-5-20251001` on the other five. Add the estimated cost and duration columns, then filter by tag, and you get the comparison:

| model | traces | tokens | total est. cost | mean duration |
|---|---|---|---|---|
| gpt-4o-mini | 5 | 1263 | $0.000350 | 1.46 s |
| claude-haiku-4-5-20251001 | 5 | 1718 | $0.004130 | 1.88 s |

Haiku came out about 12x more expensive on identical diffs and slightly slower per review (0.4 s), and it wrote longer answers (1718 tokens against 1263). Your numbers will differ slightly from run to run, but the shape should hold. Click a trace to see the diff in the input, and the `llm` span underneath for provider, model, usage and cost. The terminal prints the same table under "Same comparison read back from Opik".

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` (or rely on a repo-root `.env` one level up).
2. Point the SDK at a running Opik, for example `opik configure --use_local`. No key is needed for a local stack.
3. `uv sync`
4. `uv run review-router`
5. Open the `litellm-code-review-router` project in Opik and filter by tag.

A run takes under 30 seconds and costs under half a cent. Add `--models openai/gpt-4.1-nano` to try other LiteLLM model strings (the default is two models).

Tests run offline, with no keys and with tracking off: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Pass a third model: `uv run review-router --models openai/gpt-4o-mini anthropic/claude-haiku-4-5-20251001 openai/gpt-4.1-nano` and see whether the new row shows up in both tables.
- Shorten the answer in `SYSTEM_PROMPT` ("one line only") and check how much of the cost gap was output tokens.
- Drop a sixth `.diff` file into `data/` (a bigger one) and watch cost per call move with input size.
- In Opik, sort the Traces tab by duration instead of cost. The ranking of models can differ.

## Gotchas we hit

**The terminal fills with `RuntimeError: no running event loop` when `OpikLogger()` is created.** In a plain synchronous script, `OpikLogger` tries to start an asyncio flush task, fails, logs a long traceback, and falls back to sending synchronously. Nothing is lost, so the traces still arrive. `tracing.py` mutes the `LiteLLM` logger and `RuntimeWarning`s only while constructing the logger:

```python
logger.setLevel(logging.CRITICAL)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", RuntimeWarning)
    litellm.callbacks = [OpikLogger()]
```

**Grouping by the span's `model` field splits or renames models.** I asked for `gpt-4o-mini`, but the `llm` span records the provider's resolved name, `gpt-4o-mini-2024-07-18`, so the table no longer matches what you configured. The fix is to label the trace yourself (`opik_context.update_current_trace(tags=[...], metadata={"model": ...})`) and group on that, which is what the report does.

## How it's put together

- `review_router/config.py`: model list, review prompt, `.env` loading, and the Opik project name.
- `review_router/diffs.py`: loads `data/*.diff` into `Diff` objects.
- `review_router/router.py`: `review_diff` (traced) calls LiteLLM; `route_all` loops models and diffs.
- `review_router/tracing.py`: installs `OpikLogger`, builds the span-nesting metadata, labels traces, flushes.
- `review_router/report.py`: aggregates per model and formats the table; `samples_from_opik` queries traces back.
- `review_router/cli.py`: the `review-router` command.
- `data/`: five small fictional diffs.
- `tests/test_logic.py`: diff loading, prompt building, aggregation, trace parsing, and a traced call with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
