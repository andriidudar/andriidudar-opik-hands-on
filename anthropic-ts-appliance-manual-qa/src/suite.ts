import { Opik, type TestSuite, type TestSuiteItem } from "opik";
import { APPLIANCE_NAMES, loadManual } from "./manuals.js";
import { ITEM_ASSERTIONS, QUESTIONS } from "./questions.js";

export const SUITE_NAME = "appliance-manual-citations";

// The quality bar every answer must clear, in plain English. An LLM judge checks each sentence
// against each answer; an item passes only if every assertion holds.
export const GLOBAL_ASSERTIONS = [
  // Without this one, an answer with no quotes at all passes the verbatim check vacuously.
  "Unless the response says the manual does not cover the question, it contains at least one excerpt wrapped in <quote> tags",
  "Every excerpt wrapped in <quote> tags in the response appears verbatim, character for character, in the manual provided as context",
  "The quoted excerpts genuinely support the factual claims made in the answer",
  "The response answers the question that was asked, and does not state any specification (number, time, temperature or rule) that is not in the manual",
];

// Items carry the question and the manual text (so the judge can check quotes) but no expected
// answers, which would let the judge cheat.
export function buildItems(): TestSuiteItem[] {
  return QUESTIONS.map(({ appliance, question }) => {
    const item: TestSuiteItem = {
      data: { appliance: APPLIANCE_NAMES[appliance], key: appliance, question, context: loadManual(appliance) },
    };
    const extra = ITEM_ASSERTIONS[question];
    if (extra) item.assertions = extra;
    return item;
  });
}

// getOrCreateTestSuite stores the suite as a versioned dataset in the project. The global
// assertions and execution policy live on the suite; item assertions live on each item.
// runsPerItem 3 / passThreshold 2 absorbs judge noise: an item passes if 2 of 3 runs pass.
export async function setUpSuite(client: Opik, projectName: string): Promise<TestSuite> {
  const suite = await client.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName,
    description: "Owner's-manual answers must quote the manual verbatim",
    globalAssertions: GLOBAL_ASSERTIONS,
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // getOrCreateTestSuite returns an existing suite as-is and ignores the options passed above, so
  // an edited assertion would silently never run. updateTestSettings pushes the current ones to
  // the suite (it creates a new suite version) before every run.
  await suite.updateTestSettings({
    globalAssertions: GLOBAL_ASSERTIONS,
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // Re-running the demo must not duplicate items.
  if (((await suite.getItemsCount()) ?? 0) === 0) await suite.insert(buildItems());
  return suite;
}
