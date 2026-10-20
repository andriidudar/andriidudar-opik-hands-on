import { describe, expect, it, vi } from "vitest";
import { MockLanguageModelV4, simulateReadableStream } from "ai/test";

let seenPrompt = "";

// Stub the model: no provider key and no network. The route still runs the
// real streamText call with the Opik telemetry settings attached.
vi.mock("@ai-sdk/openai", () => ({
  openai: () =>
    new MockLanguageModelV4({
      doStream: async (options) => {
        seenPrompt = JSON.stringify(options.prompt);
        return {
          stream: simulateReadableStream({
            chunks: [
              { type: "text-start", id: "t" },
              { type: "text-delta", id: "t", delta: "Water when the top 5 cm is dry." },
              { type: "text-end", id: "t" },
              {
                type: "finish",
                finishReason: { unified: "stop", raw: "stop" },
                usage: {
                  inputTokens: { total: 10, noCache: 10, cacheRead: 0, cacheWrite: 0 },
                  outputTokens: { total: 8, text: 8, reasoning: 0 },
                },
              },
            ],
          }),
        };
      },
    }),
}));

import { POST } from "../src/routes/api/chat/+server";

describe("POST /api/chat", () => {
  it("streams a reply grounded in the retrieved note, with tracking disabled", async () => {
    const request = new Request("http://localhost/api/chat", {
      method: "POST",
      body: JSON.stringify({
        id: "chat-1",
        messages: [
          { id: "m1", role: "user", parts: [{ type: "text", text: "How often do I water my monstera?" }] },
        ],
      }),
    });
    const res = await POST({ request });
    const body = await res.text();
    expect(res.status).toBe(200);
    expect(body).toContain("Water when the top 5 cm is dry.");
    expect(seenPrompt).toContain("Monstera deliciosa"); // retrieval reached the model
  });
});
