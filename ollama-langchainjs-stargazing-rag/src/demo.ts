import path from "node:path";
import { fileURLToPath } from "node:url";
import { ChatOllama, OllamaEmbeddings } from "@langchain/ollama";
import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";
import { CHAT_MODEL, EMBED_MODEL, OLLAMA_BASE_URL, PROJECT, TOP_K } from "./config.js";
import { buildChain } from "./chain.js";
import { buildIndex, loadDocs } from "./ingest.js";
import { makeSearchTool } from "./retriever.js";

const DOCS_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../docs");

export const QUESTIONS = [
  "What was the seeing and limiting magnitude on the Messier marathon night?",
  "When should we cancel an observing night because of the weather?",
  "Which loaner telescope should a new member borrow, and who books it?",
  "What is the club's policy on drone photography?", // not in the log: tests the "does not say" path
];

async function main() {
  // One Opik client for the whole run; the callback handler shares it so flush() covers every trace.
  const client = new Opik({ projectName: PROJECT });

  // Ingest: all embedding calls go to the local Ollama server. These calls are not part of any trace.
  const embeddings = new OllamaEmbeddings({ baseUrl: OLLAMA_BASE_URL, model: EMBED_MODEL });
  const docs = await loadDocs(DOCS_DIR);
  const store = await buildIndex(docs, embeddings);
  console.log(`Indexed ${docs.length} log sections with ${EMBED_MODEL}`);

  const llm = new ChatOllama({ baseUrl: OLLAMA_BASE_URL, model: CHAT_MODEL, temperature: 0 });
  const chain = buildChain(makeSearchTool(store, TOP_K), llm).withConfig({ runName: "ask_observing_log" });

  for (const question of QUESTIONS) {
    // A fresh OpikCallbackHandler per question: the outermost run becomes one trace named
    // "ask_observing_log"; the tool run becomes a tool span and the Ollama call an llm span.
    const handler = new OpikCallbackHandler({ client, projectName: PROJECT });
    const answer = await chain.invoke(question, { callbacks: [handler] });
    console.log(`\nQ: ${question}\nA: ${answer.trim()}`);
  }

  // Traces are sent in the background; flush before exit or the last ones can be lost.
  await client.flush();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
