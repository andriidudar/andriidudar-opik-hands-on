# dspy-claim-verification

**A fact-checker that learns its own output format, with the before and after sitting in one Opik test suite.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![DSPy](https://img.shields.io/badge/DSPy-3.x-8B0000?style=flat)
![Opik SDK](https://img.shields.io/badge/Opik%20SDK-2.2.105-2f54eb?style=flat)

Claim-checking pipelines break in a boring way: the model reasons fine, but its answers
come back as "The claim is supported by the fact sheet." when downstream code needs
`SUPPORTED | evidence: L07`. You can fix that by hand-tuning a prompt, or you can let DSPy
find worked examples that teach the format. Either way you need numbers. This project gives
you them: one Opik test suite, run once against the raw program and once against the compiled one.

## What you'll build

An offline fact-checker for a made-up archipelago, the Republic of Tamarind Cay. `data/almanac.txt`
holds 14 numbered lines (`L01` ... `L14`). Given a claim, the program must answer on one line:

```
SUPPORTED | evidence: L07
REFUTED | evidence: L13
NOT ENOUGH INFO | evidence: none
```

The DSPy signature says only "decide whether the claim is supported". The format exists nowhere in the
instructions. A `ClaimVerifier` module (a `ChainOfThought` on `gpt-4o-mini`) is evaluated on nine held-out
claims, three per verdict. `BootstrapFewShot` then compiles it from nine labelled training claims with a
regex-and-label metric (no judge tokens), and the suite runs again.

## See it in Opik

Open the **`dspy-claim-verification`** project. In **Traces** you will see two kinds of rows from a clean run:
18 `evaluation_task` traces (nine per suite run) and 9 standalone `ClaimVerifier` traces (the first probe
claim plus the teacher attempts BootstrapFewShot made while compiling). Expand any trace and the DSPy
module graph is the span tree: `evaluation_task > task > ClaimVerifier > ChainOfThought > Predict > LM: openai - gpt-4o-mini`.
All 27 LM spans carry token usage and estimated cost. Compare the LM input of an uncompiled trace with a
compiled one: the compiled prompt contains six worked examples (reasoning plus a strict-format verdict), the
uncompiled one none. `log_graph=True` on the callback also attaches the module graph to the trace.

Then open the **dspy-claim-verification** test suite and its two experiments,
`uncompiled` and `compiled`. In my run:

| run | items passed |
|---|---|
| uncompiled | 0 / 9 |
| compiled | 8 / 9 |

The uncompiled answers are things like `Supported` or `The claim is not supported by the fact sheet.`, so the
format assertion fails on every item, even when the verdict is right. Compiled, the format assertion passes 9/9
and eight verdicts are correct. The one miss is honest: "Most residents live outside Port Selwyn" came back
`SUPPORTED | evidence: L02` although L02 says 61% live there, so the correct verdict is REFUTED. Numbers wobble between
runs (earlier runs of mine landed at 6/9 with four demos and 9/9 with six), because compilation and the LLM judge
are both stochastic.

## Run it yourself

1. `cd dspy-claim-verification`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep it in a parent `.env`, which `main.py` also reads).
3. Point the Python SDK at your Opik (`opik configure`, or a `~/.opik.config`).
4. `uv sync`
5. `uv run main.py` (about one minute, a few cents)
6. Open the project in Opik as described above.

Offline tests, no keys and no tracking: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `max_bootstrapped_demos` to 2. A demo set with no REFUTED example tends to teach the format but botch that verdict; watch which assertion drops.
- Add a claim to `data/claims.json` that is only partly covered by the almanac and see which way the program leans.
- Loosen `ANSWER_FORMAT` in `verifier.py` to accept lowercase, recompile, and see whether the metric still picks demos that carry the strict form.
- Open a teacher trace (a standalone `ClaimVerifier` trace) and compare its LM input with an evaluation trace: the teacher prompt has labelled demos, the plain one doesn't.

## Gotchas we hit

**Re-running leaves empty `uncompiled` / `compiled` experiments behind.**
Deleting a project's traces to get clean counts does not delete the experiments `run_tests` created, so each re-run adds
another pair with 0 traces. Remove them with
`client.rest_client.experiments.delete_experiments_by_id(ids=[...])` for experiments whose `trace_count` is 0.

## How it's put together

- `main.py`: configures DSPy with `OpikCallback`, builds the test suite, runs it uncompiled, compiles, runs it again.
- `verifier.py`: the `ClaimVerifier` module, the strict-format regex, the parser and the compile-time metric (no Opik code).
- `data/almanac.txt`: the numbered fictional fact sheet.
- `data/claims.json`: nine training claims and nine held-out test claims with gold verdict and evidence line.
- `tests/test_verifier.py`: offline tests for the parser, metric, data consistency and a traced task call under a stub LM.
- `pyproject.toml`, `.env.example`, `.gitignore`: uv project (opik pinned to 2.2.105), key template, ignores.

*built with Opik · inspired by Opik's examples and documentation*
