import Anthropic from "@anthropic-ai/sdk";
import { track } from "opik";
import { APPLIANCE_NAMES, type Appliance, loadManual } from "./manuals.js";

export const MODEL = "claude-haiku-4-5-20251001";

const client = new Anthropic({ baseURL: "https://api.anthropic.com" });

function systemPrompt(appliance: Appliance): string {
  return `You answer questions about the ${APPLIANCE_NAMES[appliance]} owner's manual, reproduced in full below.

Rules:
- Answer only from the manual. If the manual does not cover the question, say so plainly instead of guessing.
- Every factual claim must be backed by a citation: a verbatim excerpt from the manual wrapped in <quote>...</quote> tags, copied character-for-character.
- Keep answers short: the answer first, then the supporting quote(s).

<manual>
${loadManual(appliance)}
</manual>`;
}

interface ClaudeReply {
  text: string;
  model: string;
  stopReason: string | null;
  usage: { inputTokens: number; outputTokens: number };
}

// There is no first-party Anthropic wrapper for the TypeScript SDK, so the call is traced by hand.
// type "llm" makes this an LLM span; enrichSpan attaches model, provider and token usage after the
// call returns, which is what lets Opik compute cost for the span.
const createMessage = track(
  {
    name: "anthropic_messages_create",
    type: "llm",
    enrichSpan: (reply: ClaudeReply) => ({
      model: reply.model,
      provider: "anthropic",
      usage: {
        prompt_tokens: reply.usage.inputTokens,
        completion_tokens: reply.usage.outputTokens,
        total_tokens: reply.usage.inputTokens + reply.usage.outputTokens,
      },
    }),
  },
  async (params: Anthropic.MessageCreateParamsNonStreaming): Promise<ClaudeReply> => {
    const response = await client.messages.create(params);
    const block = response.content[0];
    return {
      text: block?.type === "text" ? block.text : "",
      model: response.model,
      stopReason: response.stop_reason,
      usage: { inputTokens: response.usage.input_tokens, outputTokens: response.usage.output_tokens },
    };
  },
) as (params: Anthropic.MessageCreateParamsNonStreaming) => Promise<ClaudeReply>;

// Root span: one trace per question, with the llm span nested inside it.
export const answerQuestion = track(
  { name: "answer_question", type: "general" },
  async (appliance: Appliance, question: string): Promise<string> => {
    const reply = await createMessage({
      model: MODEL,
      max_tokens: 1024,
      system: systemPrompt(appliance),
      messages: [{ role: "user", content: question }],
    });
    return reply.text;
  },
) as (appliance: Appliance, question: string) => Promise<string>;
