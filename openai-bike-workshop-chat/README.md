<div align="center">

# Bike Workshop Chat

**`openai-bike-workshop-chat`**

*A repair-shop assistant that quotes jobs, finds open slots and checks parts, with every conversation, tool call and dollar of cost visible in Opik.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-3.35-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.2.105-2f54eb?style=flat)](https://github.com/comet-ml/opik)

</div>

---

A chat assistant that calls tools produces a lot of API traffic per customer message: one completion to decide which tool to call, the tool itself, then a second completion to word the answer. Looked at as raw logs, "what did that conversation cost, and which answer made the customer unhappy?" is hard to answer. This example is a chat assistant for a fictional shop, Spoke & Sprocket Cycle Works, built on the plain OpenAI SDK, and it shows how three Opik features answer that question: threads, per-turn cost, and a feedback score logged after the run.

## What you'll build

A small Python package (`bikeshop/`) with a CLI entry point. The assistant runs a tool-calling loop against `gpt-4o-mini` with three tools over a JSON file of shop data: `get_repair_quote` (labor, parts, bike-type surcharge, out-of-stock warnings), `check_service_slots` and `lookup_part`. The demo plays two scripted customers, three messages each, then logs a thumbs-up on one conversation and a thumbs-down on the other.

## See it in Opik

Open the `openai-bike-workshop-chat` project. The demo leaves **6 traces**, all named `chat-turn`, one per customer message.

- **Threads tab.** Two threads, `commuter-brake-job` and `mtb-full-service`, three turns each. Open one and you read it like a chat transcript instead of three unrelated rows.
- **A single trace.** Click any `chat-turn`. In our run a turn looked like `chat-turn` (general) containing two `chat_completion_create` llm spans and one tool span (`get_repair_quote`, `check_service_slots` or `lookup_part`) with the arguments the model chose and the dict it got back. The one turn that quoted two jobs and checked stock had three llm spans and two tool spans.
- **Cost per turn.** The traces table has token and estimated cost columns. In our run a turn cost between $0.00013 and $0.00030 (about $0.0012 for all six). Prompt tokens climb within a thread (651 on the first brake turn, 1,649 on the second) because every call re-sends the history and the tool results.
- **Feedback score.** The last turn of each conversation carries a `customer-satisfaction` score: 1.0 on `commuter-brake-job`, 0.0 on `mtb-full-service`, each with a reason. Sort or filter the traces table on that column to jump to the unhappy conversation. The thumbs are simulated in `cli.py`; in a real shop they would come from a button in the chat widget.

## Run it yourself

From the folder `openai-bike-workshop-chat/` with a local Opik running and `OPENAI_API_KEY` in a `.env` (here or in a parent folder):

1. `cp .env.example .env` and add your key.
2. `uv sync`
3. `uv run bikeshop` (the scripted demo, about 15 seconds)
4. Open the project in Opik and visit Threads, then Traces.
5. Offline tests: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

Opik settings come from `~/.opik.config`. If you do not have one, set `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` in `.env`.

## Poke around

- `uv run bikeshop --interactive` and chat yourself. Each session is a new thread named `interactive-<id>`. Ask about brake pads and watch the out-of-stock warning flow from the tool span into the answer.
- In `bikeshop/cli.py`, flip the verdicts in `DEMO_VERDICTS`, rerun, and see which trace gets the 0.0.
- Change `MODEL` in `bikeshop/assistant.py` to `gpt-4.1-mini` and compare per-turn cost with the table above.
- Edit `data/shop.json` (empty a day's slots, change the labor rate) and compare the tool span outputs.

## Gotchas we hit

- **"Sorry, I could not finish that request." on any availability question, and four `check_service_slots` tool spans in one trace, each with an empty `open_slots` and a 2023 date.** The model had no idea what day it was, so it guessed dates one by one and exhausted the tool-round limit. Fix: put the date in the system prompt (`Today is 2026-10-30`) and tell it to call `check_service_slots` with no date to list everything. The tool-span chain in the trace is what made the cause obvious.
- **`AttributeError: 'NoneType' object has no attribute 'id'` in unit tests.** `opik_context.get_current_trace_data()` returns `None` when `OPIK_TRACK_DISABLE=true`, so code that reads the trace id for feedback crashes. Fix: `trace = opik_context.get_current_trace_data(); self.last_trace_id = trace.id if trace else None`.
- **Traces land in "Default Project".** The project name is read when `opik` is first imported. Fix: set `os.environ["OPIK_PROJECT_NAME"]` in `bikeshop/__init__.py`, before any module imports opik.
- **Feedback score call finds no trace.** Traces are sent in the background, so `log_traces_feedback_scores` can race the upload. Fix: call `opik.flush_tracker()` first, as `log_feedback` does.

## How it's put together

- `bikeshop/__init__.py` pins the Opik project name.
- `bikeshop/cli.py` is the entry point: scripted demo, `--interactive`, simulated thumbs, final flush.
- `bikeshop/assistant.py` is the tool-calling chat loop; it wraps the client with `track_openai` and sets the `thread_id`.
- `bikeshop/tools.py` holds the three tools (tool spans), their schemas and the dispatcher.
- `bikeshop/feedback.py` builds and logs the `customer-satisfaction` scores.
- `bikeshop/data.py` loads `data/shop.json`, the fictional prices, stock and slots.
- `tests/test_app.py` covers quotes, slots, parts, bad tool input, a stubbed traced turn with tracking disabled, and the score payload; `tests/conftest.py` disables tracking.

---

*built with Opik · inspired by Opik's examples and documentation*
