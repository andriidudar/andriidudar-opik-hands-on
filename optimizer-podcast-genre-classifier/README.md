# optimizer-podcast-genre-classifier

![python](https://img.shields.io/badge/python-3.12+-blue) ![opik](https://img.shields.io/badge/opik-2.2.105-orange) ![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2.0-orange)

**Let an optimizer rewrite your prompt, then read the score curve and keep the winner in Opik's prompt library.**

A podcast app needs to file each episode under one genre. The prompt that does it is a hand-written
guess, and you don't know if it's any good until you score it. This example scores a baseline prompt on
30 invented episode blurbs, lets Opik's `MetaPromptOptimizer` propose better ones within a small budget,
and stores the best prompt as a new version in the prompt library.

## What you'll build

- `data/episodes.json`: 30 made-up blurbs labeled `true-crime`, `comedy`, `science`, `history`,
  `business`, `wellness`, `sports` or `fiction`. About a third are cross-genre on purpose: a comedian
  hosting a real heist, a sleepy bedtime history lesson, a sports story that is really about money. The
  labeling rule is "subject beats tone and format".
- `classifier.py`: the baseline prompt, an exact-match metric and a plain classify function (no Opik).
- `main.py`: loads the dataset into Opik, saves the baseline as prompt v1, runs the optimizer
  (gpt-4o-mini for both the task and the prompt-writing model, 10 trials), prints the score curve, saves
  the winner as v2, then uses it on three unseen blurbs through a traced OpenAI client.

## See it in Opik

Open the `optimizer-podcast-genre-classifier` project (the run prints a project-pinned link too).

- **Optimization runs**: one run with 11 trials: the baseline (0.633) and 10 candidate prompts. In my run
  the best trial scored 0.667, so the curve is nearly flat: one more blurb out of 30 was right. Several
  candidates scored lower than the baseline (0.567 at the lowest). That is the honest shape of a small
  budget on a model that already does most of the job.
- **Traces**: 339 traces. 330 are `evaluation_task` (11 scored passes over 30 blurbs, each with an `llm`
  span), the rest are the optimizer's own reasoning calls and 3 `classify_episode` traces from the final
  step, each holding one `llm` span (`gpt-4o-mini`, about 90 tokens, about $0.000014).
- **Prompts**: `podcast-genre-classifier` has two versions: v1, the hand-written baseline, and v2, the
  optimizer's rewrite ("Respond with only the single word representing the genre").
- **Datasets**: `optimizer-podcast-genre-classifier-episodes`, 30 items.

## Run it yourself

1. Put `OPENAI_API_KEY` in a `.env` one directory above this folder (the repo root), or export it.
   Have a local Opik running (or set `OPIK_URL_OVERRIDE`).
2. From this folder:
   ```bash
   uv sync
   uv run main.py
   ```
   It takes a few minutes and costs a few cents. The optimizer prints `total llm cost: unavailable`
   (see Gotchas); the real cost is the 330 + 3 gpt-4o-mini calls plus the prompt-writing calls.
3. Offline tests, no keys, no Opik traffic:
   ```bash
   env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
   ```

## Poke around

- Raise `MAX_TRIALS` in `main.py` or `prompts_per_round` and see whether the curve moves.
- Delete `task_context_columns` from the optimizer call: it then never sees the correct labels and often
  can't discover that `crime` should be `true-crime`.
- Make the metric stricter (drop `normalize`) and watch which trials collapse.
- Add a ninth genre to `episodes.json` and re-run; the dataset de-duplicates, so only new rows are added.

## Gotchas we hit

**Every trial scores 0.000 and the model asks "Please provide the description".** A dataset column named
`description` did not reach the prompt: items came back with only `genre` and `id`. Renaming the column to
`blurb` (and the placeholder to `{blurb}`) fixed it. Dataset-level `description=` is a separate argument.

**A flat curve with all-zero candidates.** With a baseline that answered in sentences, the prompt-writing
model never saw the outputs, only scores, and every rewrite stayed wrong. Passing
`task_context_columns=["blurb", "genre"]` lets it see the expected labels, and a metric that returns a
`ScoreResult` with a `reason` documents what went wrong. Gains still stay small and vary run to run.

**`get_run_link()` can look empty.** It opens in whichever project the UI last showed. `main.py` builds a
link from the optimization's own project id instead.

**`create_chat_prompt(change_description=...)` showed `None`.** The call accepted it, but reading the
versions back through the REST client returned `None` for the note, so the library history is told by
version order, not by notes.

**`total llm cost: unavailable`.** `result.llm_cost_total` came back `None` for this run; per-span cost
on the `classify_episode` llm spans is populated.

## How it's put together

- `main.py`: dataset, prompt library, optimizer run, score curve, winner saved, traced tryout.
- `classifier.py`: baseline prompt, `genre_accuracy`, `explain`, `classify`, data loader.
- `data/episodes.json`: the 30 labeled blurbs.
- `tests/test_classifier.py`: dataset sanity, metric and explanation text.
- `tests/test_tracing.py`: `classify` with a stub client, also through `opik.track` with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
