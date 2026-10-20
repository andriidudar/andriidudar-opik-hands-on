import type { Document } from "@langchain/core/documents";
import type { VectorStore } from "@langchain/core/vectorstores";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

export const SEARCH_TOOL_NAME = "search_observing_log";

export function formatContext(docs: Document[]): string {
  return docs
    .map((d, i) => `[${i + 1}] (${d.metadata.title} / ${d.metadata.section})\n${d.pageContent}`)
    .join("\n\n");
}

/**
 * Retrieval as a named LangChain tool. When the chain calls it, OpikCallbackHandler opens a
 * span of type "tool" called search_observing_log, with the query as input and the fetched
 * sections as output. That is the explicit, always-visible retrieval span: it does not depend on
 * how a given callback handler treats raw retriever runs.
 */
export function makeSearchTool(store: VectorStore, k: number) {
  return tool(
    async ({ query }) => {
      const docs = await store.similaritySearch(query, k);
      return formatContext(docs);
    },
    {
      name: SEARCH_TOOL_NAME,
      description: "Find the sections of the club's observing log most relevant to a question.",
      schema: z.object({ query: z.string() }),
    },
  );
}
