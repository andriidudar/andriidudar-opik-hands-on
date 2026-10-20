# prompt-library-museum-labels

*A wall-label prompt with two immutable versions in Opik's prompt library, and one test suite that scores both: 0% for v1, 100% for v2.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Opik SDK 2.2.105](https://img.shields.io/badge/Opik%20SDK-2.2.105-2f54eb?style=flat)
![OpenAI gpt-4o-mini](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat)

A museum label has hard constraints. It must fit on a card, follow a house style, carry the accession number, and say only what the catalogue record says. "Write an engaging label" satisfies none of that, and a prompt edit that fixes one rule can quietly break another. This example treats the label-writing prompt as a versioned asset: stored in Opik's prompt library, edited by publishing a new version, and judged by the same rules every time.

## What you'll build

A small package, `museum_labels`, with four subcommands:

| Command | What it does |
|---|---|
| `publish` | Pushes `prompts/v1.txt` and `prompts/v2.txt` to the prompt library as `museum-label-writer`, safely repeatable |
| `diff` | Prints the v1 to v2 unified diff using the texts stored in the library |
| `suite` | Runs one test suite (five fictional artefacts from `data/artefacts.json`) against v1, then v2 |
| `generate` | Writes labels with a library version of your choice, as traced calls |

v1 is a vague "write an engaging label" prompt. v2 adds the real rules: at most 60 words, present tense, no exclamation marks, never "you", facts from the record only, a provenance line, and a closing `Acc. no.` line. The suite checks those rules with four global assertions plus one item-level assertion per artefact (three records have no provenance and must say so, two have one and must not claim otherwise). The judge is `gpt-4o`; labels come from `gpt-4o-mini`.

## See it in Opik

Open the **prompt-library-museum-labels** project. In the **Prompts** area you will find `museum-label-writer` with exactly two versions, v1 (commit `d15c5859`) and v2 (commit `55f2e4a6`). Select both and use the compare view to see the diff: v1 is two lines, v2 replaces them with a rule list. Running `publish` again does not add a third version.

Next, open **Experiments**. There are two: `museum-label-writer-v1` and `museum-label-writer-v2`, each with five items and each linked to its prompt version. In my run v1 passed 0 of 5 items and v2 passed 5 of 5. The v1 labels ran 206 to 293 words against the 60-word limit, so no item cleared the bar. The v2 labels ran 41 to 48 words. Comparing the two runs side by side shows which rules the edit fixed.

Finally, open **Traces**. Each suite item is an `evaluation_task` trace holding a `task` span, a nested `write_label_from_library` span, the `gpt-4o-mini` llm span (tokens and cost filled in), and the judge's `llm_judge` spans on `gpt-4o`. The trace metadata carries `prompt_version`, `prompt_commit`, and `local_checks`, an offline pass/fail dict for the same rules computed without a model. The extra trace named `write_label_from_library` comes from the `generate` command.

## Run it yourself

1. `cd prompt-library-museum-labels`
2. `cp .env.example .env` and add `OPENAI_API_KEY` (or use a repo-root `.env`, which is loaded automatically). Opik is read from `~/.opik.config`; this example was run against a local self-hosted stack.
3. `uv sync`
4. `uv run python -m museum_labels publish`
5. `uv run python -m museum_labels diff`
6. `uv run python -m museum_labels suite` (about 20 to 30 seconds)
7. `uv run python -m museum_labels generate --accession 1993.2.11`

Expected summary from step 6:

```
museum-label-writer v1: 0% pass rate (0/5 items passed)
museum-label-writer v2: 100% pass rate (5/5 items passed)
```

Judge scoring and sampling vary between runs, so treat v2 as "all or nearly all" rather than a guaranteed 100%.

## Poke around

- Delete the line "Output the label text only" from a copy of `prompts/v2.txt`, publish it as a third version, and see which assertion starts failing.
- Raise the strictness: change the limit to 35 words in the prompt and the assertion text and see whether `gpt-4o-mini` can hold it.
- Add a sixth artefact to `data/artefacts.json` with a tricky provenance, then re-run `suite`. The suite deduplicates items, so only the new one is added.
- Open a v1 trace and compare `local_checks` with the judge's scores. They agree on the word limit.

## Gotchas we hit

**`publish` leaves three versions after you run it twice.** `create_prompt` only skips creation when the new text matches the *latest* version. Re-publishing v1's text after v2 exists adds a v3. I confirmed it by creating `alpha`, `beta`, `alpha` under one name and getting three versions. Fix: compare against the whole history before creating, as `library.publish()` does:

```python
existing = {p.prompt for p in client().get_prompt_history(PROMPT_NAME, project_name=PROJECT_NAME)}
if text not in existing:
    client().create_prompt(name=PROMPT_NAME, prompt=text, project_name=PROJECT_NAME, ...)
```

**v2 passes only 3 of 5 items, and the failing labels all say "Provenance not recorded." on artefacts that do have a provenance.** My first v2 said "if the record gives no provenance, say so", and the model stamped the sentence on every label. The item-level assertions caught it. Fix: spell out both branches in the prompt (`Provenance not recorded.` for `(none recorded)`, otherwise `Provenance: <text>`), which is the version in `prompts/v2.txt`.

**Editing `prompts/v2.txt` after publishing does not replace v2.** Versions are immutable, so the new text becomes v3 and the old v2 stays. The Python client has no `delete_prompt`, so while iterating I removed the prompt through the REST client and republished:

```python
ps = client.rest_client.prompts.get_prompts(name="museum-label-writer", size=10).content
client.rest_client.prompts.delete_prompts_batch(ids=[p.id for p in ps])
```

Only do that on a scratch prompt; in real use you publish v3 and keep the history.

## How it's put together

- `museum_labels/data.py`: loads the catalogue and prompt files, renders a record as the user message.
- `museum_labels/generate.py`: sets the Opik project, wraps the OpenAI client with `track_openai`, writes one label.
- `museum_labels/library.py`: idempotent `publish`, version lookup, and the unified diff.
- `museum_labels/suite.py`: the test suite (assertions, items), the traced per-version task, and the `run_tests` call.
- `museum_labels/checks.py`: offline rule checks (word count, accession line, house style, provenance).
- `museum_labels/cli.py`, `museum_labels/__main__.py`: the subcommands.
- `prompts/v1.txt`, `prompts/v2.txt`: the two prompt versions. `data/artefacts.json`: five fictional records.
- `tests/test_labels.py`: offline tests with the model stubbed. Run `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

---

*built with Opik · inspired by Opik's examples and documentation*
