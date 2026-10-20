import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import path from "node:path";
import { loadNotes, retrieve, buildSystemPrompt } from "$lib/notes";
import "$lib/server/env";

const notes = loadNotes(path.resolve(process.cwd(), "data"));

export async function POST({ request }: { request: Request }) {
  // The Chat class from @ai-sdk/svelte posts the full history each turn.
  const { messages }: { messages: UIMessage[] } = await request.json();

  const userText = (m: UIMessage) =>
    m.parts.map((p) => (p.type === "text" ? p.text : "")).join(" ");
  const recent = messages.filter((m) => m.role === "user").slice(-2).map(userText).join(" ");

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: buildSystemPrompt(retrieve(notes, recent)),
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
