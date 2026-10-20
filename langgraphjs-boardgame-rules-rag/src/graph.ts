import { BaseRetriever } from "@langchain/core/retrievers";
import { Document } from "@langchain/core/documents";
import type { CallbackManagerForRetrieverRun } from "@langchain/core/callbacks/manager";
import type { Embeddings } from "@langchain/core/embeddings";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";
import { Annotation, END, START, StateGraph } from "@langchain/langgraph";
import { topK, type RuleChunk } from "./rules.js";

export const SYSTEM_PROMPT =
  "You are a rules referee for three board games. Answer the player's question using ONLY the " +
  "rule excerpts below. If the excerpts do not contain the answer, say exactly: " +
  "\"The rulebooks don't say.\" Keep the answer to 1-3 sentences.";

export function formatContext(chunks: string[]): string {
  return chunks.map((c, i) => `[${i + 1}] ${c}`).join("\n");
}

// A BaseRetriever subclass: LangChain emits retriever start/end events for it, which the
// OpikCallbackHandler turns into a span carrying the query and the returned documents.
export class RulesRetriever extends BaseRetriever {
  lc_namespace = ["boardgame", "retrievers"];
  private index: { vec: number[]; item: RuleChunk }[] = [];

  constructor(private readonly embeddings: Embeddings, private readonly k = 3) {
    super();
  }

  async load(chunks: RuleChunk[]): Promise<void> {
    const vecs = await this.embeddings.embedDocuments(chunks.map((c) => c.text));
    this.index = chunks.map((item, i) => ({ item, vec: vecs[i]! }));
  }

  async _getRelevantDocuments(query: string, _rm?: CallbackManagerForRetrieverRun): Promise<Document[]> {
    const qv = await this.embeddings.embedQuery(query);
    return topK(qv, this.index, this.k).map(
      (c) => new Document({ pageContent: c.text, metadata: { game: c.game, section: c.section } }),
    );
  }
}

const State = Annotation.Root({
  question: Annotation<string>(),
  context: Annotation<string[]>(),
  answer: Annotation<string>(),
});

export function buildGraph(retriever: RulesRetriever, llm: BaseChatModel) {
  return new StateGraph(State)
    // Each node becomes a chain span named after the node ("retrieve", "generate") in the trace.
    .addNode("retrieve", async (state, config) => {
      // Passing `config` forwards the run's callbacks, so the retriever run is nested under this node.
      const docs = await retriever.invoke(state.question, config);
      return { context: docs.map((d) => d.pageContent) };
    })
    .addNode("generate", async (state, config) => {
      // The chat model call inside the node is logged as an llm span with the prompt, tokens and cost.
      const res = await llm.invoke(
        [
          { role: "system", content: `${SYSTEM_PROMPT}\n\nExcerpts:\n${formatContext(state.context)}` },
          { role: "user", content: state.question },
        ],
        config,
      );
      return { answer: String(res.content) };
    })
    .addEdge(START, "retrieve")
    .addEdge("retrieve", "generate")
    .addEdge("generate", END)
    .compile();
}
