# pydantic-ai-calendar-extraction

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-2.58-E92063?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.105-2f54eb?style=flat)

**An email-to-calendar agent whose test suite is built to catch the fields it makes up.**

A typed `CalendarEvent` always looks finished. It has a title, a date, a time, a
timezone, a few attendees. Whether each of those values came from the email, or from
the model filling a blank with something plausible, is invisible when you skim the
output. "Lunch Friday at 12:30" quietly gains a timezone. "Coffee sometime next week"
gains an exact date. "Whole team please" becomes an attendee named `Whole team`.

This example gives you a way to see that, and to keep seeing it after every prompt
or model change.

## What you'll build

- A Pydantic AI agent (`gpt-4o-mini`) that reads one email and returns a
  `CalendarEvent`: title, date, start and end time, timezone, location, meeting link,
  attendees. Every field except the title may be null.
- Six fictional emails in `data/emails.json`, each chosen to tempt a different
  invention: a missing timezone, a call with only a Zoom link, a reschedule thread
  with the old time quoted underneath, a coffee invitation with no date at all, an
  all-hands addressed to nobody in particular.
- Tracing through Pydantic AI's OpenTelemetry output. `logfire` is used only as the
  bridge, and its spans go straight to Opik's OTLP endpoint.
- Two layers of hallucination checks. A deterministic one (`grounding.py`) tests
  whether each non-null value is backed by words in the email. An Opik test suite
  adds plain-language assertions that an LLM judge scores, global rules plus
  expectations per email.
- A package with a small CLI instead of a single script: `calendar-extraction extract`
  prints events, `calendar-extraction suite` runs the suite.

## See it in Opik

Open the **pydantic-ai-calendar-extraction** project. After one suite run it
holds 6 traces named `evaluation_task`, one per email. Open any of them and the tree
has 7 spans: the suite's own `extraction_task`, then `invoke_agent calendar_extractor`
containing a `chat gpt-4o-mini` span of type `llm` (about 400 tokens, roughly
$0.0001), next to the judge's `completion` span (`gpt-5-nano`, also type `llm`, with
usage and cost). The agent call and the judge verdict for an email live in the same
trace.

Click the `chat gpt-4o-mini` span for the thing you came for: the input shows the
system prompt and the rendered email, the output shows the tool call carrying the
event JSON. In the `vague-coffee` trace the email says only "sometime next week" and
the output holds `"date":"2026-03-12"`. A date the email never gave.

Next open **Test Suites** and the suite of the same name: 6 items and 4 global
assertions. Its one experiment, `extract-gpt-4o-mini`, shows a 67% pass rate (4 of 6
emails). The failures from the run I kept:

- `vague-coffee` fails because of that invented date. The `ungrounded_fields` entry in
  the task output says `['date']` before the judge even speaks.
- `reschedule-thread` fails twice over: the agent kept `"Same room"` as the location
  instead of resolving it to Room B from the quoted message, and it returned an empty
  attendee list for a message between two named people.
- `product-sync`, `vendor-call`, `lunch-no-timezone` and `all-hands` pass. The
  timezone-free lunch is the interesting one, since `timezone` and `end_time` stayed null.

Expect the exact split to move between runs: across the runs I did, the same email
sometimes passed and sometimes failed (the reschedule thread kept "Same room" as the
location in most runs and carried over "Room B" in one; `all-hands` listed an attendee
named "Whole team" in two runs and left the list empty in this one). That drift is the point of
having a suite.

## Run it yourself

From this folder (`pydantic-ai-calendar-extraction/`):

1. `uv sync`
2. Put `OPENAI_API_KEY` in a `.env` here or in the repo-root `.env` (see `.env.example`).
3. Make sure a local Opik is running at `http://localhost:5173`, with workspace `default`.
4. `uv run calendar-extraction extract` prints the six extracted events and sends their traces (6 standalone `invoke_agent` traces; the counts above are for a project holding only the suite run).
5. `uv run calendar-extraction suite` runs the test suite (about 30 seconds, a fraction
   of a cent) and prints the pass rate, each email's verdict and the experiment link.
6. Offline tests, no keys and no Opik needed:
   `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

To target Opik Cloud instead, set `OPIK_OTEL_ENDPOINT=https://www.comet.com/opik/api/v1/private/otel/v1/traces`
and add an `Authorization` header in `tracing.py`.

## Poke around

- Edit the system prompt in `agent.py` to say "always give your best guess for every
  field" and re-run the suite. The invented-value failures should spread to more emails.
- Set `CALENDAR_MODEL=openai:gpt-4.1-mini` and run again. Each run is a new experiment
  on the same suite, so the pass rates compare side by side.
- Add a seventh email to `data/emails.json` with its own assertions, for example one
  that says "9ish" and see whether `09:00` counts as grounded.
- The judge is noisy. Add `global_execution_policy={"runs_per_item": 3, "pass_threshold": 2}`
  to `update_test_settings` in `suite.py` and an email passes only if two of three runs do.

## Gotchas we hit

**The trace's Input column is a block of `gen_ai.aggregated_usage...` attributes, not the email.**
Pydantic AI's root span is exported with its OTel attributes as input. The email text
is inside `pydantic_ai.all_messages` there, and plainly visible on the `chat gpt-4o-mini`
span. Open that span when you want the prompt and the event side by side.

**Every email shows up twice: 12 traces for 6 emails, and the agent trace is not on the experiment item.**
With only the OTLP exporter, `run_tests` records its own `evaluation_task` trace with
the judge, while the agent's `invoke_agent` span arrives as a separate root trace. The
fix is to also register Opik's span processor, which stamps the active Opik trace id
onto OTel spans started inside it:

```python
from opik.integrations.otel import OpikSpanProcessor
logfire.configure(additional_span_processors=[OpikSpanProcessor(), BatchSpanProcessor(exporter)])
```

After that the project holds exactly 6 traces, with the agent call nested in each.

**I reworded a global assertion and the next run still used the old wording.**
`get_or_create_test_suite` returns the existing suite as it was first created, so a
changed `GLOBAL_ASSERTIONS` list is ignored. Push the list explicitly on every run:
`suite.update_test_settings(global_assertions=GLOBAL_ASSERTIONS)`. It does nothing if
the text is unchanged.

**An email fails although the output looks fine.**
The judge reads each assertion literally. The first version of my "fields the email
does not mention are null" rule failed `all-hands`, whose timezone and location are
stated, because the judge applied the rule to all four fields at once. State the
exception inside the assertion ("fields the email does state may be filled in") and
keep the verdict reasons open in the experiment while you tune wording.

## How it's put together

- `src/calendar_extraction/schema.py`: the `CalendarEvent` model.
- `src/calendar_extraction/agent.py`: the Pydantic AI agent, its prompt, the model switch.
- `src/calendar_extraction/emails.py`: loads `data/emails.json` and renders an email as agent input.
- `src/calendar_extraction/tracing.py`: the logfire to Opik OTLP bridge, with the project header and flush.
- `src/calendar_extraction/grounding.py`: offline checks that each value is supported by the email text.
- `src/calendar_extraction/suite.py`: the Opik test suite, its assertions and the `run_tests` call.
- `src/calendar_extraction/cli.py`, `__main__.py`: the `extract` and `suite` commands.
- `data/emails.json`: the six fictional emails with per-email expectations.
- `tests/test_grounding.py`: time, date and phrase grounding, and invented-field detection.
- `tests/test_agent.py`: the suite's items and task with a stubbed model, including a run through the instrumented agent with no exporter.

*built with Opik · inspired by Opik's examples and documentation*
