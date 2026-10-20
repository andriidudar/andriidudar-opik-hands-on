# temporal-py-film-festival-screening

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Temporal](https://img.shields.io/badge/temporalio-Python_SDK-000000)
![Opik](https://img.shields.io/badge/opik-2.2.105-2f54eb)

**One Opik trace that starts in your client process, continues inside a Temporal worker, and shows the activity that failed before it succeeded.**

A festival gets submissions, a workflow screens them, and some steps are flaky. Temporal makes the workflow durable: a failed activity is retried and the workflow carries on. The cost is that the work now runs in two OS processes, the starter that kicks it off and the worker that executes it. Ordinary tracing gives you two unrelated pieces. This example stitches them back into one trace and keeps the failed attempt visible.

## What you'll build

A `ScreenSubmission` workflow over three fictional submissions in `data/submissions.json`:

1. `check_eligibility` applies runtime, year and fee rules (no LLM).
2. `screen_synopsis` asks `gpt-4o-mini` for genre, themes, content flags and a 1-5 fit score.
3. `assign_screener` picks a reader from a roster. It fails on its first attempt every time ("roster service timed out") and Temporal retries it after one second.
4. `write_decision_letter` has the model draft a short letter for the decision.

Ineligible submissions (SUB-2043) stop after step 1.

Opik documents a [Temporal integration](https://www.comet.com/docs/opik/integrations/temporal) for Python, based on Temporal's OpenTelemetry `TracingInterceptor` exported to Opik's OTLP endpoint. This example does it by hand instead, with Opik's own SDK, so the OpenAI calls can use `track_openai` and share the trace: the starter opens a `@track` span, takes `opik_context.get_distributed_trace_headers()` (trace id and parent span id), and puts them in the workflow input. The workflow forwards them to every activity, and each activity passes them to its `@track` function as `opik_distributed_trace_headers`. There is no Temporal interceptor, so Temporal's own StartWorkflow/RunActivity spans do not appear, only your code's.

## See it in Opik

Open the `temporal-py-film-festival-screening` project and the Traces tab. A clean run gives three traces named `screen_submission`, one per submission.

Open one for an eligible film (for example "The Lighthouse Keeper's Radio"). It has 8 spans in one tree, and the spans from `check_eligibility` down were created by the worker process, not the starter:

- `screen_submission` (general, starter process)
- `check_eligibility` (tool)
- `screen_synopsis` (general) containing one `chat_completion_create` llm span: about 210 tokens, around $0.00007
- `assign_screener` (tool), **two spans**: attempt 1 is marked as an error (`ConnectionError`, "Screener roster service timed out"), attempt 2 succeeds. Their metadata holds `temporal_attempt` and the workflow id.
- `write_decision_letter` (general) containing a second `chat_completion_create` llm span, about 190 tokens

The rejected film's trace has just two spans, `screen_submission` and `check_eligibility`, because the workflow stops there. The whole run costs well under a cent.

## Run it yourself

You need `uv`, the `temporal` CLI (the demo starts its own in-memory dev server on port 7241 and stops it when done), an OpenAI key in `.env` (here or in a parent folder) and a running Opik.

1. `cp .env.example .env` and add `OPENAI_API_KEY`.
2. `uv run demo`
3. Open the project in Opik and look at the newest traces.
4. `uv run python verify.py` prints every trace's span tree with errors, attempts, tokens and cost.

`uv run demo` starts the dev server, spawns `python -m screening.worker` as a second process, runs the three submissions from the starter, then flushes and shuts everything down.

## Poke around

- In `screening/activities.py` change `attempt == 1` to `attempt <= 3` and raise `maximum_attempts` in `workflows.py`: the trace gains two more red `assign_screener` spans.
- Drop `trace_headers` from one activity call in `workflows.py`. That activity's spans land in a separate one-span trace instead of the tree.
- Edit the synopsis of SUB-2042 to something bleak and watch the `fit_score` and the decision letter change in the llm spans.
- Run `uv run python -m screening.worker` in one terminal against your own `temporal server start-dev` and start workflows from another.

## Gotchas we hit

**Extra traces appear in the project after running the tests.** Calling the activities in a test with tracking on sends real traces to Opik (we got four stray one-span traces next to the demo's three). Set `OPIK_TRACK_DISABLE=true` for tests.

**`TypeError: _check_eligibility() got an unexpected keyword argument 'opik_distributed_trace_headers'` in tests.** With tracking enabled `@track` strips that keyword before calling your function; with `OPIK_TRACK_DISABLE=true` it passes it straight through. Declare it on every function that receives headers: `async def _assign_screener(genre: str, opik_distributed_trace_headers: dict | None = None)`. The offline tests now call the traced activities with tracking disabled to guard this.

## How it's put together

- `screening/workflows.py` the deterministic workflow; forwards trace headers.
- `screening/activities.py` the four activities, `@track` functions and the `track_openai` client.
- `screening/logic.py` offline rules: eligibility, screener pick, decision thresholds.
- `screening/starter.py` opens the root span and starts a workflow with headers in its input.
- `screening/worker.py` the worker process; flushes Opik on shutdown.
- `screening/demo.py` one-command dev server, worker and starter.
- `screening/config.py`, `models.py` constants and dataclasses; `data/submissions.json` the fixture.
- `verify.py` queries Opik and prints the trace trees.
- `tests/` offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
