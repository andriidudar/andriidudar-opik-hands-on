import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import type { Runnable } from "@langchain/core/runnables";
import { RunnableLambda } from "@langchain/core/runnables";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";
import { SEARCH_TOOL_NAME, type makeSearchTool } from "./retriever.js";

export const PROMPT = ChatPromptTemplate.fromMessages([
  [
    "system",
    "You are the logbook assistant of the Fernhill Astronomical Society. Answer ONLY from the " +
      "observing-log excerpts below. If they do not contain the answer, reply exactly: " +
      "\"The log does not say.\" Keep the answer to two sentences.\n\nExcerpts:\n{context}",
  ],
  ["human", "{question}"],
]);

/**
 * A bare `tool.invoke({ query })` returns a plain string, and OpikCallbackHandler logs a tool
 * span's output only when it is a ToolMessage, so the span would show an input and an empty
 * output. Invoking with a ToolCall makes LangChain return a ToolMessage, which fills the output.
 */
export const toolCall = (query: string) => ({
  type: "tool_call" as const,
  id: "call_search",
  name: SEARCH_TOOL_NAME,
  args: { query },
});

/**
 * question -> search tool -> prompt -> local chat model -> string.
 * Passing the `config` the step receives into tool.invoke hands the tool the run's callbacks, so
 * the tool span is nested under the same trace (here: ask_observing_log > gather_context > tool).
 */
export function buildChain(
  searchTool: ReturnType<typeof makeSearchTool>,
  llm: BaseChatModel,
): Runnable<string, string> {
  const retrieve = RunnableLambda.from(async (question: string, config) => ({
    question,
    context: (await searchTool.invoke(toolCall(question), config)).content as string,
  })).withConfig({ runName: "gather_context" });

  return retrieve.pipe(PROMPT).pipe(llm).pipe(new StringOutputParser());
}
