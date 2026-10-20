import { describe, expect, it } from "vitest";
import { chunkRulebook, cosine, topK } from "../src/rules.js";
import { averagePrecision, ContextPrecision } from "../src/contextPrecision.js";
import { formatContext, buildGraph, RulesRetriever } from "../src/graph.js";
import { FakeEmbeddings, FakeListChatModel } from "@langchain/core/utils/testing";
import { track } from "opik";

const BOOK = "# Toy Game (2 players)\n\n## Setup\nPlace the board.\nDeal cards.\n\n## Winning\nMost points wins.\n";

describe("rulebook chunking", () => {
  it("makes one chunk per section, prefixed with the title", () => {
    const chunks = chunkRulebook(BOOK);
    expect(chunks.map((c) => c.section)).toEqual(["Setup", "Winning"]);
    expect(chunks[0]!.game).toBe("Toy Game");
    expect(chunks[0]!.text).toBe("Toy Game (2 players) - Setup: Place the board. Deal cards.");
  });
});

describe("vector helpers", () => {
  it("ranks by cosine similarity", () => {
    expect(cosine([1, 0], [1, 0])).toBeCloseTo(1);
    const items = [
      { vec: [0, 1], item: "far" },
      { vec: [1, 0.1], item: "near" },
    ];
    expect(topK([1, 0], items, 1)).toEqual(["near"]);
  });
});

describe("context precision metric", () => {
  it("rewards relevant chunks that rank early", () => {
    expect(averagePrecision([true, false, false])).toBe(1);
    expect(averagePrecision([false, true])).toBe(0.5);
    expect(averagePrecision([false, false])).toBe(0);
  });

  it("scores through a stubbed judge", async () => {
    const metric = new ContextPrecision(async (_q, chunk) => chunk.includes("yes"));
    const res = await metric.score({ input: "q", context: ["yes a", "no b"] });
    expect(res).toMatchObject({ name: "context_precision", value: 1, reason: "relevant chunks by rank: YN" });
  });
});

describe("graph with tracking disabled", () => {
  it("runs retrieve -> generate with stub models, and a tracked function still works", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    const retriever = new RulesRetriever(new FakeEmbeddings(), 1);
    await retriever.load(chunkRulebook(BOOK));
    const graph = buildGraph(retriever, new FakeListChatModel({ responses: ["Most points."] }) as never);
    const out = await graph.invoke({ question: "Who wins?" });
    expect(out.answer).toBe("Most points.");
    expect(out.context).toHaveLength(1);
    expect(formatContext(out.context)).toMatch(/^\[1\] Toy Game/);

    // track() wraps a function in an Opik span; with tracking disabled it just calls through.
    const tracked = track({ name: "double" }, async (n: number) => n * 2);
    expect(await tracked(4)).toBe(8);
  });
});
