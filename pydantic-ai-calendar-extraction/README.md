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

Open the **pydantic-ai-calendar-extraction** project. After one suite run it holds 12 traces: 6 `evaluation_task` traces from the suite
(each with the judge's `completion` span, type `llm`, `gpt-5-nano`, with usage and
cost) and 6 separate `invoke_agent calendar_extractor` traces, one per email, each
with a `chat gpt-4o-mini` span of type `llm` (about 400 tokens, roughly $0.0001).

Click the `chat gpt-4o-mini` span for the thing you came for: the input shows the
system prompt and the rendered email, the output shows the tool call carrying the
event JSON. In the `vague-coffee` trace the email says only "sometime next week" and
the output holds `"date":"2026-03-09"`. A date the email never gave.

Next open **Test Suites** and the suite of the same name: 6 items and 4 global
assertions. Its one experiment, `extract-gpt-4o-mini`, shows a 50% pass rate (3 of 6
emails). The failures from the run I kept:

- `vague-coffee` fails because of that invented date. The `ungrounded_fields` entry in
  the task output says `['date']` before the judge even speaks.
- `all-hands` fails because the agent listed `"Whole team"` as an attendee. The
  deterministic check misses that one (both words are in the email), the judge catches
  it.
- `reschedule-thread` fails on its attendees: the agent returned an empty list for a
  message between two named people, and the judge flagged it under the "attendees are
  named in the email" rule.
- `product-sync`, `vendor-call` and `lunch-no-timezone` pass. The timezone-free lunch
  is the interesting one, since `timezone` and `end_time` stayed null.

Expect the exact split to move between runs: across the runs I did, the same email
sometimes passed and sometimes failed (the reschedule thread kept "Same room" as the
location once, and carried over "Room B" another time). That drift is the point of
having a suite.

## Run it yourself

From this folder (`pydantic-ai-calendar-extraction/`):

1. `uv sync`
2. Put `OPENAI_API_KEY` in a `.env` here or in the repo-root `.env` (see `.env.example`).
3. Make sure a local Opik is running at `http://localhost:5173`, with workspace `default`.
4. `uv run calendar-extraction extract` prints the six extracted events and sends their traces.
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
