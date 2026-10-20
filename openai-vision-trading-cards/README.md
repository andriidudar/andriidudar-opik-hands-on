# Trading Card Reader

**`openai-vision-trading-cards`** · a vision model reads stats off cards that were never in its training data, and Opik keeps the card next to every answer.

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.2.105-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

When a model misreads a picture, the text-only trace is useless. You see `"name": "Voltpuft"` and have no idea whether the model slipped or the print was bad. You need the pixels beside the output. And when you test an image pipeline, a suite that passes 100% on tidy inputs tells you nothing about the crooked, faded, thumb-smudged photos users will actually send.

This example reads typed stats (name, set number, rarity, card type, HP, attack name and damage, defense, ability name and text) from trading cards that are invented and drawn on the spot, including cards that are rotated, low-contrast, or smudged on purpose.

## What you'll build

- `cardgen.py` draws eight fictional cards with Pillow from `data/cards.json`: four clean, one rotated 14 degrees on a table, one pale-ink-on-pale-stock, one rotated and pale, and one with a grey thumbprint over the defense stat. The PNGs land in `generated/` (git-ignored) on every run.
- `extract.py` sends a card to `gpt-4o-mini` as image input and gets ten fields back through a strict JSON schema. Fields the model cannot read must come back as `null`.
- `main.py` builds an Opik **test suite** from the same JSON that drew the cards: three plain-language assertions per card plus three format rules for all cards. An LLM judge grades them. The suite is allowed to fail.
- `scoring.py` is a second, deterministic opinion: exact field-by-field matching, printed next to the judge's verdict.

## See it in Opik

Open the project **openai-vision-trading-cards**. After one run it holds **8 traces**, each named `evaluation_task` (the suite creates one per card). Open one, for example the Voltpuff trace.

- **Span tree:** seven spans in all. `extraction_task` contains `extract_card`, which contains `chat_completion_create` (type `llm`). Beside them are the judge's spans: `llm_judge`, `llm_judge_arg_validation`, `metrics_calculation` and a `completion` llm span.
- **Usage:** the extraction span reports about **25,800 total tokens** and roughly **$0.002**. A 600x840 card at `detail: "high"` is almost all image tokens, which is where the cost of a vision call hides. The judge call is about 1,500 tokens.
- **Attachments tab on the trace:** `voltpuff.png`, the file the model was sent, previewable in place. You can see the grey thumbprint over "Defense" and compare it with the span output, where `defense` is `null` and `name` is `"Voltpuft"`.

Then open **Experiments** and pick `gpt-4o-mini-card-stats`. The run described here passed **7 of 8** cards, hard ones included: the pale-ink Dunewyrm, the rotated Frostmoth, and the rotated-and-pale Glimmerfox. The one failure was the smudged card, and the console shows it at 80% field accuracy, wrong on `name` ("Voltpuft", a letter the model made up) and `defense` (`null`, which is the honest answer but still a missing stat). An earlier run of the same code passed 6 of 8: Voltpuff failed again, and Frostmoth failed because the model returned `"Ice type"` as the card type instead of `"Ice"`. The pass rate moves between runs, so treat one suite run as a sample.

## Run it yourself

1. Install: `uv sync`
2. Put `OPENAI_API_KEY` in a `.env` here or one folder up (see `.env.example`). Opik needs no key against a local install configured with `opik configure --use_local`.
3. Run: `uv run main.py`

It takes about 25 seconds and costs a few cents. Draw the cards without calling anything: `uv run cardgen.py`.

Offline tests (no keys, no Opik):

```
env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
```

## Poke around

- Open `generated/voltpuff.png`, then change `"smudge": "defense"` to `"hp"` in `data/cards.json` and rerun. Does the model still return `null`, or does it guess?
- Add `"rotation": 70` to a clean card and watch where the failures start.
- Change `"detail": "high"` to `"low"` in `extract.py` and compare the token counts on the `llm` span.
- Tighten the system prompt about `card_type` (copy only the word before "type") and see whether the Frostmoth miss stays gone across several runs.

## Gotchas we hit

**`openai.OpenAIError: Missing credentials` while running the tests.** `OpenAI()` was created at import time, so merely importing `extract.py` needed a key. The fix is to build the wrapped client on first use:

```python
@functools.cache
def get_client() -> OpenAI:
    return track_openai(OpenAI(), project_name=PROJECT_NAME)
```

**Each card costs about 25,800 tokens.** For `gpt-4o-mini`, image tokens are billed at a steep multiplier, so one PNG at `detail: "high"` is far more than the visible text. Watch the usage column on the `llm` span before scaling a vision pipeline to thousands of images.

**A null is a correct answer that still fails the suite.** The prompt asks for `null` on unreadable values, and the smudged card's `defense` came back `null`. The assertion still says "defense is 20", so the item fails. That is the right call for an answer key built from ground truth, but if you want "refuses to guess" to count as a pass, write that into the card's assertion.

## How it's put together

- `data/cards.json`: the eight invented cards, their expected stats, and the style (clean, rotated, low contrast, smudged) that drives drawing.
- `cardgen.py`: Pillow renderer, including the rotation, fade and thumbprint effects.
- `extract.py`: the vision call; `track_openai` client, `@opik.track` function, image attachment.
- `suite.py`: global rules and per-card assertions, built from `cards.json`.
- `scoring.py`: deterministic field-by-field comparison.
- `main.py`: draws cards, runs the suite, prints verdicts and the experiment link.
- `tests/test_cards.py`: six offline tests, including a traced `extract_card` call with a stubbed client and tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
