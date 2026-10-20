import { describe, expect, it } from "vitest";
import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";
import { Document } from "@langchain/core/documents";
import { FakeEmbeddings, FakeListChatModel } from "@langchain/core/utils/testing";
import { buildChain, PROMPT, toolCall } from "../src/chain.js";
import { buildIndex, loadDocs, splitSections } from "../src/ingest.js";
import { formatContext, makeSearchTool, SEARCH_TOOL_NAME } from "../src/retriever.js";

describe("ingest", () => {
  it("splits a log file into one document per section", () => {
    const docs = splitSections("a.md", "# Title\n\n## One\nfirst\n\n## Two\nsecond\n");
    expect(docs.map((d) => d.metadata.section)).toEqual(["One", "Two"]);
    expect(docs[0]?.metadata.title).toBe("Title");
  });

  it("loads the shipped docs/ corpus", async () => {
    const docs = await loadDocs(new URL("../docs", import.meta.url).pathname);
    expect(docs.length).toBeGreaterThan(15);
    expect(docs.some((d) => d.pageContent.includes("Messier"))).toBe(true);
  });
});

describe("retrieval and chain (stubbed models, no Ollama, no Opik)", () => {
  it("formats context with numbered sources", () => {
    const out = formatContext([new Document({ pageContent: "body", metadata: { title: "T", section: "S" } })]);
    expect(out).toBe("[1] (T / S)\nbody");
  });

  it("runs the search tool and the full chain with tracking disabled", async () => {
    const store = await buildIndex(
      [new Document({ pageContent: "Saturn rose at 01:15", metadata: { title: "Log", section: "May" } })],
      new FakeEmbeddings(),
    );
    const searchTool = makeSearchTool(store, 1);
    expect(searchTool.name).toBe(SEARCH_TOOL_NAME);
    expect(await searchTool.invoke({ query: "saturn" })).toContain("Saturn rose");
    // A ToolCall comes back as a ToolMessage, the shape OpikCallbackHandler needs to log the span output.
    const msg = await searchTool.invoke(toolCall("saturn"));
    expect(msg.content).toContain("Saturn rose");
    expect(msg.tool_call_id).toBe("call_search");

    const llm = new FakeListChatModel({ responses: ["Saturn rose at 01:15."] });
    const answer = await buildChain(searchTool, llm).invoke("When did Saturn rise?");
    expect(answer).toBe("Saturn rose at 01:15.");
  });

  it("puts the excerpts and the question into the prompt", async () => {
    const msgs = await PROMPT.formatMessages({ context: "EXCERPT", question: "Q?" });
    expect(String(msgs[0]?.content)).toContain("EXCERPT");
    expect(String(msgs[1]?.content)).toBe("Q?");
  });

  it("runs with OpikCallbackHandler attached when tracking is disabled", async () => {
    // OPIK_TRACK_DISABLE=true makes the SDK client a no-op, so the handler never needs a server.
    process.env.OPIK_TRACK_DISABLE = "true";
    const handler = new OpikCallbackHandler({ client: new Opik({ projectName: "unit-test" }) });
    const store = await buildIndex([new Document({ pageContent: "x", metadata: {} })], new FakeEmbeddings());
    const llm = new FakeListChatModel({ responses: ["ok"] });
    const chain = buildChain(makeSearchTool(store, 1), llm);
    expect(await chain.invoke("q", { callbacks: [handler] })).toBe("ok");
  });
});
