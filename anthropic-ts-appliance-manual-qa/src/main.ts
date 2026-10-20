import "./env.js";
import { Opik, flushAll, runTests } from "opik";
import { checkCitations } from "./citations.js";
import { loadManual, type Appliance } from "./manuals.js";
import { answerQuestion } from "./qa.js";
import { setUpSuite } from "./suite.js";

const projectName = process.env.OPIK_PROJECT_NAME ?? "anthropic-ts-appliance-manual-qa";
const client = new Opik({ projectName });
const suite = await setUpSuite(client, projectName);

// runTests runs the task once per item per run, then has the judge check every assertion.
// Each task call is a normal answer_question trace; the experiment links to those traces.
const result = await runTests({
  testSuite: suite,
  model: "claude-haiku-4-5", // the LLM judge (override of the suite default); Claude, so one key
  projectName,
  taskThreads: 3,
  experimentName: process.env.LOOSE_PROMPT === "1" ? "loose-prompt" : "strict-citation-prompt",
  task: async (item) => {
    const data = item as { key: Appliance; question: string };
    // input must be exactly what the model saw, so the judge can compare quotes with the context.
    const input = { question: data.question, context: loadManual(data.key) };
    return { input, output: await answerQuestion(data.key, data.question) };
  },
});

console.log(`\nPass rate: ${((result.passRate ?? 0) * 100).toFixed(0)}% (${result.itemsPassed}/${result.itemsTotal} items passed)`);
for (const r of result.itemResults.values()) {
  const first = r.testResults[0];
  const out = first?.testCase.taskOutput as { input: { question: string; context: string }; output: string };
  const local = checkCitations(out.output, out.input.context);
  console.log(`  [${r.passed ? "PASS" : "FAIL"}] ${out.input.question}  (${r.runsPassed}/${r.runsTotal} runs, local check: ${local.quotes.length === 0 ? "no quotes" : local.missing.length === 0 ? "all quotes verbatim" : `${local.missing.length} quote(s) not in manual`})`);
  for (const run of r.testResults) {
    for (const s of run.scoreResults) {
      if (s.scoringFailed || s.value !== 1) console.log(`      failed: ${s.name} - ${s.reason}`);
    }
  }
}
if (result.experimentUrl) console.log(`\nView the run: ${result.experimentUrl}`);

// Flush so the last traces, scores and the experiment reach Opik before the process exits.
await flushAll();
