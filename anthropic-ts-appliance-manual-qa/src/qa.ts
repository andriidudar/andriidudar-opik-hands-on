import Anthropic from "@anthropic-ai/sdk";
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

export async function answerQuestion(appliance: Appliance, question: string): Promise<string> {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: systemPrompt(appliance),
    messages: [{ role: "user", content: question }],
  });
  const block = response.content[0];
  return block?.type === "text" ? block.text : "";
}
