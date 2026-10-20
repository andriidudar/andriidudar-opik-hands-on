"""Let the Opik Agent Optimizer rewrite the genre prompt, then save the winner to the prompt library."""

import os
import pathlib

PROJECT_NAME = "optimizer-podcast-genre-classifier"
# Read at client creation: optimizer runs, traces and prompts all land in this project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
os.environ.pop("OPENAI_BASE_URL", None)  # talk to the public API, not a local proxy
os.environ.pop("OPENAI_API_BASE", None)

import dotenv

dotenv.load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

import opik
from openai import OpenAI
from opik.integrations.openai import track_openai
from opik.evaluation.metrics import score_result
from opik_optimizer import ChatPrompt, MetaPromptOptimizer

from classifier import BASELINE_SYSTEM, HELD_OUT, classify, explain, genre_accuracy, load_episodes

MODEL = "openai/gpt-4o-mini"  # LiteLLM naming, used for the task and for the prompt-writing model
DATASET_NAME = "optimizer-podcast-genre-classifier-episodes"
LIBRARY_PROMPT_NAME = "podcast-genre-classifier"
MAX_TRIALS = 10  # cap on candidate prompts the optimizer may score: the cost budget

opik_client = opik.Opik()

# A dataset is what the optimizer scores each candidate against. Opik de-duplicates
# identical rows, so re-running reuses the dataset instead of growing it.
episodes = load_episodes()
dataset = opik_client.get_or_create_dataset(
    name=DATASET_NAME, description="30 invented podcast blurbs labeled with one of 8 genres"
)
dataset.insert([{"blurb": e["description"], "genre": e["genre"]} for e in episodes])



def genre_metric(dataset_item: dict, llm_output: str) -> score_result.ScoreResult:
    # A ScoreResult carries a `reason`. The optimizer shows reasons to its prompt-writing
    # model, so it learns *what* went wrong ("answered a sentence"), not just a number.
    return score_result.ScoreResult(
        name="genre_accuracy",
        value=genre_accuracy(dataset_item, llm_output),
        reason=explain(dataset_item, llm_output),
    )


prompt = ChatPrompt(
    name="podcast-genre-classifier",
    system=BASELINE_SYSTEM,
    user="{blurb}",  # filled from the dataset's "blurb" column
    model=MODEL,
)

# Library version 1 = the baseline, saved before optimizing so the prompt page
# shows the whole story. create_chat_prompt adds a version only if content changed.
opik_client.create_chat_prompt(
    name=LIBRARY_PROMPT_NAME,
    messages=[
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": "{{blurb}}"},
    ],
    change_description="Baseline hand-written prompt (pre-optimization)",
    project_name=PROJECT_NAME,
)

# The optimizer evaluates the baseline, asks the reasoning model why it fails, and
# scores new candidates. Each evaluation is an Opik trial; together they form the
# optimization run with its score curve.
optimizer = MetaPromptOptimizer(
    model=MODEL,
    prompts_per_round=3,
    # Show the prompt-writing model example rows including the correct genre, so it
    # can see which exact labels the dataset expects.
    task_context_columns=["blurb", "genre"],
    seed=42,
    verbose=1,
)
result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=genre_metric,
    n_samples=len(episodes),
    max_trials=MAX_TRIALS,
    project_name=PROJECT_NAME,
)

initial = result.initial_score if result.initial_score is not None else 0.0
best = result.score

# The score curve: baseline, then every candidate prompt the optimizer scored, in
# order. The same curve is drawn on the optimization's page in Opik.
print("\ntrial     score  best-so-far")
best_so_far = initial
print(f"baseline  {initial:.3f}  {best_so_far:.3f}  " + "#" * round(initial * 30))
for rnd in result.history or []:
    for t in rnd["trials"]:
        best_so_far = max(best_so_far, t["score"])
        label = f"trial {t['trial_index'] + 1}"
        print(f"{label:<9} {t['score']:.3f}  {best_so_far:.3f}  " + "#" * round(t["score"] * 30))

cost = result.llm_cost_total
print("\n" + "=" * 64)
print(f"baseline accuracy : {initial:.3f}")
print(f"best accuracy     : {best:.3f}  ({best - initial:+.3f})")
print(f"trials completed  : {result.details.get('trials_completed')}  (budget: {MAX_TRIALS})")
print(f"total llm cost    : {'$%.4f' % cost if cost is not None else 'unavailable'}")

# get_run_link() lands in whichever project the UI last showed, so the run can look
# empty. Build a link pinned to the optimization's own project instead.
opt = opik_client.rest_client.optimizations.get_optimization_by_id(result.optimization_id)
ui_base = opik_client.config.url_override.rstrip("/").removesuffix("/api")
print(f"optimization run  : {ui_base}/{opik_client.config.workspace}/projects/{opt.project_id}"
      f"/optimizations/{result.optimization_id}")
print("=" * 64)

# Only a real improvement earns library version 2.
if best > initial:
    messages = result.prompt.get_messages()
    for m in messages:  # optimizer placeholders are {x}; the library uses mustache {{x}}
        m["content"] = m["content"].replace("{blurb}", "{{blurb}}")
    # Adds version 2 of the library prompt; v1 (the baseline) stays beside it.
    opik_client.create_chat_prompt(
        name=LIBRARY_PROMPT_NAME,
        messages=messages,
        change_description=f"MetaPromptOptimizer winner: accuracy {initial:.3f} -> {best:.3f} on {DATASET_NAME}",
        project_name=PROJECT_NAME,
    )
    print(f"\nSaved the winner to the prompt library as '{LIBRARY_PROMPT_NAME}'.\n")
    print(messages[0]["content"])
    # The optimizer sometimes quotes the placeholder inside the system text; outside the
    # optimizer nothing fills it in, so point it at the user message instead.
    winner = messages[0]["content"].replace("'{{blurb}}'", "below").replace("{{blurb}}", "below")
else:
    print("\nNo improvement: the library keeps only v1.")
    winner = BASELINE_SYSTEM

# Use the winner on unseen blurbs. track_openai turns each completion into an llm
# span with tokens and cost; @opik.track groups it into one trace per episode.
traced_openai = track_openai(OpenAI(), project_name=PROJECT_NAME)
traced_classify = opik.track(name="classify_episode", project_name=PROJECT_NAME)(classify)
print("\nWinner on unseen blurbs:")
for text in HELD_OUT:
    print(f"  {traced_classify(traced_openai, winner, text):<12} <- {text[:60]}")

opik.flush_tracker()  # traces are sent in the background; flush so none are lost on exit
