import { config as loadEnv } from "dotenv";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { Opik, evaluate, Hallucination } from "opik";
import { OpikCallbackHandler } from "opik-langchain";
import { buildGraph, RulesRetriever } from "./graph.js";
import { loadRulebooks } from "./rules.js";
import { ContextPrecision } from "./contextPrecision.js";
import { QUESTIONS } from "./questions.js";

const here = dirname(fileURLToPath(import.meta.url));
// Pick up the repo-root .env (provider keys, Opik URL) when running from the example folder.
loadEnv({ path: join(here, "../../.env"), quiet: true });

const PROJECT = "langgraphjs-boardgame-rules-rag";
process.env.OPIK_URL_OVERRIDE ??= "http://localhost:5173/api/";
process.env.OPIK_WORKSPACE ??= "default";
process.env.OPIK_PROJECT_NAME = PROJECT;

const MODEL = "gpt-4o-mini";
const JUDGE = "gpt-4.1-mini";

async function main() {
  const retriever = new RulesRetriever(new OpenAIEmbeddings({ model: "text-embedding-3-small" }), 3);
  await retriever.load(loadRulebooks(join(here, "../data")));
  const llm = new ChatOpenAI({ model: MODEL, temperature: 0 });
  const graph = buildGraph(retriever, llm);

  // One Opik client for datasets/experiments; the callback handler shares it so traces and
  // experiment items land in the same project on the same server.
  const client = new Opik({ projectName: PROJECT });

  // Part 1: answer a few questions. OpikCallbackHandler (passed per call) logs each invoke as one
  // trace: chain spans for retrieve/generate, a retriever span, and an llm span with usage.
  console.log("== Traced demo questions ==");
  for (const q of QUESTIONS.slice(0, 4)) {
    const handler = new OpikCallbackHandler({ client, projectName: PROJECT, metadata: { stage: "demo" } });
    const out = await graph.invoke({ question: q.question }, { callbacks: [handler] });
    await handler.flushAsync();
    console.log(`Q: ${q.question}\nA: ${out.answer}\n`);
  }

  // Part 2: a dataset and an experiment. getOrCreateDataset + insert is idempotent per dataset name,
  // and the dataset is what makes experiment runs comparable.
  const dataset = await client.getOrCreateDataset<{ input: string; reference: string }>(
    "boardgame-rules-questions",
  );
  await dataset.clear();
  await dataset.insert(QUESTIONS.map((q) => ({ input: q.question, reference: q.reference })));

  // Hallucination ships with the SDK (judge: gpt-4.1-mini, since gpt-4o-mini flagged correct "the rulebooks don't say" answers as hallucinations). ContextPrecision does not exist in the TS SDK, so ours
  // (src/contextPrecision.ts) is a BaseMetric subclass that asks gpt-4o-mini whether each chunk helps.
  const judgeLlm = new ChatOpenAI({ model: MODEL, temperature: 0 });
  const contextPrecision = new ContextPrecision(async (question, chunk) => {
    const res = await judgeLlm.invoke(
      `Question: ${question}\n\nRule excerpt: ${chunk}\n\nDoes this excerpt contain information needed to answer the question? Reply with only YES or NO.`,
    );
    return String(res.content).trim().toUpperCase().startsWith("YES");
  });

  // evaluate() runs the task on every dataset item, logs one trace per item, applies the metrics
  // and creates an experiment linked to the dataset, with hallucination_metric and context_precision columns.
  const result = await evaluate({
    dataset,
    client,
    experimentName: `rules-rag-${MODEL}-k3`,
    projectName: PROJECT,
    experimentConfig: { model: MODEL, retrievalK: 3, embeddings: "text-embedding-3-small" },
    scoringMetrics: [new Hallucination({ model: JUDGE }), contextPrecision],
    task: async (item) => {
      const out = await graph.invoke({ question: String(item.input) });
      return { output: out.answer, context: out.context };
    },
  });

  console.log(`== Experiment ${result.experimentName} (${result.experimentId}) ==`);
  const sums: Record<string, number[]> = {};
  for (const t of result.testResults) {
    for (const s of t.scoreResults) (sums[s.name] ??= []).push(s.value);
  }
  for (const [name, vals] of Object.entries(sums)) {
    console.log(`${name}: mean ${(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2)} over ${vals.length} items`);
  }

  // Traces are sent in the background; flush before the process exits or the last ones are lost.
  await client.flush();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
