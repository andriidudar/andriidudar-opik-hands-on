# openai-agents-pet-adoption

*A shelter front desk of four agents, and the trace that shows which one dropped the ball.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![openai-agents](https://img.shields.io/badge/openai--agents-0.22%2B-412991?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.35-2f54eb?style=flat)

When a chat made of several agents gives a bad answer, the reply alone doesn't say whether the router, the specialist or a tool was at fault. This example is a small animal-shelter front desk. A triage agent hands visitors to an adoption, foster or surrender specialist, and each specialist calls tools over a made-up shelter database. Opik's `OpikTracingProcessor` records the handoffs and every tool call, and a shared `group_id` folds each visitor's turns into one thread.

## What you'll build

- `Front Desk Triage` routes only; it has three handoffs and no tools.
- `Adoption Specialist` has `find_animals` and `reserve`; `Foster Coordinator` has `list_foster_slots`; `Surrender Intake` has `book_surrender`.
- Tool logic lives in `shelter.py` as plain functions over a handful of fictional animals, so it is unit-testable and needs no API.
- `main.py` plays three scripted conversations (five turns) on `gpt-4o-mini`. Each turn runs inside `trace(..., group_id=<conversation id>)`.
- The third conversation is deliberately a trap, to give you something to find in the trace.

## See it in Opik

Open the `openai-agents-pet-adoption` project. In **Traces** there are five rows named `Shelter front desk`, one per turn, each with 11-12 spans. Open one: the tree is `Task` > `Front Desk Triage` (one `Turn` with an `llm` span `Response`) > `Handoff` > the specialist (for example `Adoption Specialist`) > its `Turn`s, with a `tool` span between them such as `find_animals` or `reserve`. Click a tool span to see the arguments the model chose (`{"animal_id":"A-101","adopter_name":"Maya Okafor"}`) and the JSON the tool returned. LLM spans show model `gpt-4o-mini-2024-07-18`, token counts and an estimated cost (about $0.00004 per call); a whole turn costs roughly $0.0001-0.0003.

Now the interesting part. In the `rehome-and-mixup` thread, turn one (rabbit surrender on Monday) shows a `book_surrender` tool span returning `{"error": "no surrender appointments on Monday", "available_days": [...]}`, and the agent correctly offers Tuesday. Turn two asks for Tuesday *and* to reserve Captain Whiskers for a sister. The triage agent hands it to `Surrender Intake` again, which has no adoption tools, and in our run it called `book_surrender` a second time with `owner_name: "Ana Reyes"` and told the visitor Captain Whiskers was reserved. Nothing was reserved, and Captain Whiskers is already adopted anyway. The reply reads fine; the span tree shows that two surrender bookings were made and `reserve` was never called.

The **Threads** tab lists three threads, `kid-friendly-dog-...` (2 turns), `foster-kittens-...` (1) and `rehome-and-mixup-...` (2). Open one to read the whole exchange in order.

A smaller one: asked about fostering a kitten, the Foster Coordinator called `list_foster_slots` with `species: "cat"`, got the 2-week cat slot, and never saw the 8-week kitten slot. The tool span input is where you notice it. Model behaviour varies between runs, so your trace may fail in a different place.

## Run it yourself

From this folder, with Opik running locally and `OPENAI_API_KEY` available (in `.env` here or one level up):

1. `cp .env.example .env` and add your key (skip if the parent folder has one).
2. `uv sync`
3. `uv run main.py` (about 25 seconds)
4. `uv run python verify.py` prints the traces, spans, threads and costs from Opik.
5. Offline tests: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Give the surrender specialist a `reserve` tool, or add a fourth specialist for "adopt and surrender in one visit", and re-run the last conversation to see the tool spans change.
- Change `list_foster_slots` to match `kitten` against both species and check the foster span.
- Edit the triage prompt to tell it to ask a clarifying question on mixed requests, and compare the handoff span.
- Set `MODEL` to `gpt-4.1-mini` and compare cost per turn in the trace list.

## Gotchas we hit

- **Everything is `general` except LLM and tool spans.** The processor maps agent, turn, handoff and task spans to `general`; that is expected, so filter by name (`Handoff`) rather than by type.
- **The `Type` filter finds no handoffs.** In the pinned versions the processor logs `Task`, agent, `Turn` and `Handoff` spans as `general`; only model calls are `llm` and function tools `tool`. Search span names (`Handoff`) instead.

## How it's put together

- `main.py` - agents, handoffs, Opik processor, scripted conversations with `group_id` threads.
- `shelter.py` - fictional animals, foster slots and the tool logic.
- `verify.py` - queries Opik and prints traces, span types, tool I/O, tokens, cost and threads.
- `tests/test_shelter.py` - offline tests for the tools and for importing the traced agents with tracking disabled.
- `pyproject.toml`, `.env.example`, `.gitignore` - setup (pins `opik==2.2.35`).

*built with Opik · inspired by Opik's examples and documentation*
