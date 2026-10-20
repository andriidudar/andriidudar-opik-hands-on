# anthropic-ts-appliance-manual-qa

*Claude answers questions about appliance manuals and has to quote them. An Opik test suite checks every quote.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Anthropic SDK](https://img.shields.io/badge/%40anthropic--ai%2Fsdk-0.135.0-191919?style=flat)
![opik](https://img.shields.io/badge/opik-2.2.105-2f54eb?style=flat)

When a bot answers from an owner's manual, a confident wrong number is worse than "I don't know": 60 minutes of cooling becomes 30, a 75 minute descale becomes 45, and someone burns a boiler. The defence is to make the model quote the manual and then check the quotes. This project does that for three fictional appliances, and the checking is an Opik test suite written in plain English.

## What you'll build

A small TypeScript app over three fictional manuals in `docs/`: the Hearthline CO-900 combi oven, the Loafwright BM-4 bread maker and the Brasa Ristretto E2 espresso machine. For each question, `claude-haiku-4-5` gets the whole manual and must wrap every claim's evidence in `<quote>` tags, copied character for character.

The Anthropic TypeScript SDK has no Opik wrapper (the opik npm package ships integrations for OpenAI, Vercel AI and LangChain, none for `@anthropic-ai/sdk`), so the Claude call is traced by hand with `track({ type: "llm" })` and an `enrichSpan` callback that attaches model, provider and token usage. Opik computes cost from those.

On top of that sits a test suite (`getOrCreateTestSuite` + `runTests`). Its quality bar is three plain-English sentences, and three questions have extra sentences of their own. Claude Haiku acts as the judge, so the whole example needs one API key. Each question runs three times and passes if at least two runs pass.

## See it in Opik

Open the project `anthropic-ts-appliance-manual-qa`. A run of the suite leaves 21 traces (7 questions x 3 runs). Open one: the tree shows the task, then `answer_question` (a general span), then `anthropic_messages_create`, an llm span with model `claude-haiku-4-5-20251001`, provider `anthropic`, about 700 prompt tokens and a cost of roughly $0.001. The judge's own calls appear in the same trace as `llm_judge` and `model.generateText` spans.

Under Evaluation > Test suites (and in the experiment `strict-citation-prompt`), each of the 7 items shows a pass or fail, and each assertion is a column with a score of 1 or 0 and the judge's reason when it is 0. A failing item links to the exact trace that produced the answer.

## Run it yourself

1. `npm install`
2. Put `ANTHROPIC_API_KEY` in a `.env` (here or one level up). The Opik settings default to a local self-hosted stack (`http://localhost:5173/api/`, workspace `default`); override with `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE`, `OPIK_PROJECT_NAME`.
3. `npm run demo`. It takes about 40 seconds.
4. `npm test` runs the offline tests with no key and no Opik.

## Poke around

- Edit an assertion in `src/suite.ts` and re-run: the suite is created once, so delete it in Opik first.
- Change a number in `docs/bread-maker.md` and see the item-level assertions react.
- Raise `runsPerItem` or set `passThreshold: 3` to make the suite stricter.
- Run with `LOOSE_PROMPT=1` to swap in a prompt without citation rules.

## How it's put together

- `src/env.ts` loads `.env` and sets Opik defaults.
- `src/qa.ts` is the Claude call, with the hand-made llm span.
- `src/citations.ts` extracts `<quote>` excerpts and checks them locally.
- `src/questions.ts` holds the questions and item-level assertions.
- `src/suite.ts` defines the global assertions and creates the suite.
- `src/main.ts` runs the suite and prints a summary.
- `tests/` has vitest tests for the citation checker, suite items and a stubbed `answerQuestion`.

*built with Opik · inspired by Opik's examples and documentation*
