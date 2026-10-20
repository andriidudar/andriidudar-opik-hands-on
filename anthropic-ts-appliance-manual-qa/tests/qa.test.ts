import { describe, expect, it, vi } from "vitest";

const create = vi.fn(async (_params: unknown) => ({
  content: [{ type: "text", text: 'Wait. <quote>wait the full 20 minutes</quote>' }],
  model: "claude-haiku-4-5-20251001",
  stop_reason: "end_turn",
  usage: { input_tokens: 10, output_tokens: 5 },
}));

// Stub the Anthropic client: no key, no network.
vi.mock("@anthropic-ai/sdk", () => ({
  default: class {
    messages = { create };
  },
}));

describe("answerQuestion (tracking disabled by vitest.config.ts)", () => {
  it("returns the model text and sends the manual in the system prompt", async () => {
    const { answerQuestion } = await import("../src/qa.js");
    const answer = await answerQuestion("espresso-machine", "How long to warm up?");
    expect(answer).toContain("<quote>wait the full 20 minutes</quote>");
    const params = create.mock.calls[0]?.[0] as { system: string };
    expect(params.system).toContain("Brasa Ristretto E2");
    expect(params.system).toContain("heat-soaked");
  });
});
