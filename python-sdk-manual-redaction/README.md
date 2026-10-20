# python-sdk-manual-redaction

![Python](https://img.shields.io/badge/python-3.12%2B-3776ab?style=flat&logo=python&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.2.105-2f54eb?style=flat)

*Redact personal data from documents, and record every step by hand with the low-level Opik client.*

Decorators and integration wrappers hide what a trace really is. Here there are none: a four-stage PII
redaction pipeline (detect, classify, redact, verify) builds its traces, spans, token usage and
feedback scores with explicit calls to `opik.Opik()`. The model calls go through the plain `openai`
client. The point is to see exactly which fields Opik needs, and what disappears when you leave one out.

## What you'll build

`pipeline.py` reads the three fictional documents in `data/` (a clinic note, a support ticket, meeting
minutes) and produces one `redact-document` trace per file:

```
redact-document            trace, tag pii-redaction, feedback: redaction_confidence, leak_check
  detect    (general)      └─ chat gpt-4o-mini   llm span: model, provider, token usage
  classify  (general)      └─ chat gpt-4o-mini   llm span
  redact    (tool)         plain string replacement, no model
  verify    (guardrail)    └─ chat gpt-4o-mini   llm span: audits the redacted text for leftovers
```

The verify stage combines a deterministic check (does any detected string survive verbatim?) with an
LLM audit. Both feed a pass/fail `leak_check` score, and the auditor's own 0 to 1 certainty becomes
`redaction_confidence`.

## See it in Opik

Open the `python-sdk-manual-redaction` project. The Traces tab shows three `redact-document` traces, each
tagged `pii-redaction`, with two feedback columns. In my run the clinic note and the support ticket scored
`leak_check = 1.0` and `redaction_confidence = 1.0`. The meeting minutes scored `leak_check = 0.0` with
confidence `0.7`: the detector found the three full names and replaced them, but the minutes also say
"Ravi to send..." and "Ilse will share...", and those bare first names survived. Open that trace, expand
`verify`, and its output lists `llm_leaks: ["Ravi", "Ilse", "[CONTACT]"]`. The first two are real. The
`[CONTACT]` entry is the auditor flagging a placeholder, a false positive worth noticing.

Expand a trace to see the span tree above. Each `chat gpt-4o-mini` span carries the resolved model name
(`gpt-4o-mini-2024-07-18`), provider `openai`, prompt and completion tokens, and an estimated cost in the
span's cost column (between $0.00003 and $0.00013 per call). The `redact` and `detect`/`classify` rows have
no cost because only spans with model, provider and usage get one. A full run is about $0.001.

## Run it yourself

1. `cd python-sdk-manual-redaction`
2. Put `OPENAI_API_KEY` in `.env` here or in a parent directory (see `.env.example`). Opik itself is read
   from `~/.opik.config`, for example a local self-hosted stack.
3. `uv run python pipeline.py`
4. Open the project in Opik and expand a trace.
5. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Run `uv run python pipeline.py --skip-flush`. It exits through `os._exit`, like a killed worker. In my run
  the first two documents had arrived (the SDK sends in background batches), but the third trace was
  incomplete: only its `detect` span and one llm span, no output, no feedback scores.
- Delete the `usage=` argument in `llm_span` and re-run. The spans still appear but the cost column is empty.
- Make `verify` stricter or looser in `VERIFY_PROMPT` and watch which documents flip `leak_check`.
- Add a fourth document with a nickname or an initial and see whether the detector catches it.

## Gotchas we hit

**Spans arrive with a null name, no model and no usage.** Calling `span.end(...)` immediately after
`trace.span(...)` prints `Calling Span.end() shortly after creation with batching enabled may cause data
loss`. In my first run the update raced the create: several spans showed `name = None` and no model, usage
or cost. Fix: send each span complete in one call, with `output`, `start_time` and `end_time` passed to
`trace.span(...)`. The same warning appears for `Trace.end()`, so the trace is re-sent at the end with
`opik_client.trace(id=trace.id, ..., output=..., end_time=...)`, which updates the row with no warning.

**The last trace is cut off when the process dies.** The client queues and batches in the background, so
a process that ends without `client.flush()` (here simulated with `--skip-flush`) loses whatever was still
queued, usually the newest trace. Fix: call `client.flush()` before exit.

**`client.search_traces(...)` did not list everything when I used it to clean up.** It returned one trace
when nine existed. For deleting leftovers between runs I used the REST list (`GET /v1/private/traces`) and
`POST /v1/private/traces/delete` instead.

## How it's put together

- `pipeline.py` - the pipeline, every trace, span, usage and feedback call, and the flush.
- `data/` - three fictional documents with invented names, numbers and addresses.
- `tests/test_pipeline.py` - offline tests for redaction order, leak check, JSON helper, and a hand-built span with tracking disabled.
- `pyproject.toml` / `.env.example` / `.gitignore` - project setup with `opik==2.2.105` pinned.

---

*built with Opik · inspired by Opik's examples and documentation*
