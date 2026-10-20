# langchain-fastapi-language-tutor

*Luz, a Spanish tutor in a chat widget, whose conversations read like chats in Opik's Threads view.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat&logo=fastapi&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.2-2f54eb?style=flat)

A chat widget talks to your backend one HTTP request at a time. Opik sees one trace per request, so a learner's ten-message practice session arrives as ten unrelated rows, and if the root run takes a dict or message list the Threads view fills up with JSON. This example is a small tutor backend where each turn is a trace, each learner is a thread, and the thread transcript is plain text in and plain text out.

## What you'll build

- A FastAPI app with `POST /chat` and a tiny static HTML widget at `/`.
- A LangChain chain: look up history and matching lesson notes, prompt, `gpt-4o-mini`, `StrOutputParser`. It takes the learner's message as a **string** and returns a **string**.
- Fictional lesson notes in `data/lessons.md`, searched by a keyword retriever that is its own traced `tool` span.
- `OpikTracer(thread_id=session_id)` on every request, so a learner's turns share one thread.
- `demo.py`, which plays two learners with three turns each through FastAPI's `TestClient`, so nothing keeps running.

## See it in Opik

Open the project `langchain-fastapi-language-tutor`. After one demo run it holds 6 traces named `tutor-turn`.

- **Threads tab:** two threads, `learner-ser-vs-estar` and `learner-cafe-trip`, each with 6 messages (3 questions, 3 answers). The first message is the learner's question and the last is Luz's final reply, as plain sentences.
- **Traces tab, open one trace:** the root `tutor-turn` has input `{"input": "<the question>"}` and output `{"output": "<the reply>"}`. Below it are `gather_context` (containing the `find_lesson_notes` tool span), `ChatPromptTemplate`, `ChatOpenAI` (an `llm` span with about 300-420 tokens and a cost near $0.00008) and `StrOutputParser`.
- `find_lesson_notes` shows the question as input and the lesson sections it picked as output, which is the first place to look when an answer ignores the teacher's notes.

## Run it yourself

1. `cd langchain-fastapi-language-tutor`
2. `cp .env.example .env` and set `OPENAI_API_KEY`. Opik uses `~/.opik.config` (run `opik configure`, or set `OPIK_URL_OVERRIDE` for a local server).
3. `uv run demo.py` (about 10 seconds, well under a cent).
4. `uv run python verify.py` prints the traces, threads and span shape.
5. For the real widget: `uv run uvicorn tutor.app:app --port 8000`, then open http://localhost:8000.

## Poke around

- Open a thread and click a later message: the trace shows the earlier turns inside `ChatOpenAI`'s input, which is the memory at work.
- Change `find_notes(question, k=2)` to `k=0` and re-run; the tutor stops quoting the lesson notes, and `find_lesson_notes` shows the empty lookup.
- Make the chain take a dict (`{"message": ...}`) and compare the Threads view.
- Swap `gpt-4o-mini` in `tutor/chain.py` for another model and compare cost per turn.

## Gotchas we hit

- **Symptom: the chain's prompt step appears as a `tool` span.** `ChatPromptTemplate` is logged with type `tool` by `OpikTracer` in opik 2.2. It is cosmetic; the model call is still the `llm` span with usage and cost.

## How it's put together

- `tutor/app.py`: FastAPI routes, builds the `OpikTracer` per request.
- `tutor/chain.py`: the string-in/string-out chain and session memory.
- `tutor/notes.py`: lesson-note loader and the traced keyword retriever.
- `data/lessons.md`: fictional lesson notes.
- `static/index.html`: the chat widget.
- `demo.py`: scripted two-learner demo; `verify.py`: prints what Opik stored.
- `tests/`: offline tests with a fake model, run with tracking disabled:
  `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
