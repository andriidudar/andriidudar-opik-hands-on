import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import path from "node:path";
import { loadNotes, retrieve, buildSystemPrompt } from "$lib/notes";
import { OpikExporter } from "opik-vercel";
import "$lib/server/env";

const notes = loadNotes(path.resolve(process.cwd(), "data"));

export async function POST({ request }: { request: Request }) {
  // The Chat class from @ai-sdk/svelte posts its chat id and the full history each turn.
  const { id, messages }: { id: string; messages: UIMessage[] } = await request.json();

  const userText = (m: UIMessage) =>
    m.parts.map((p) => (p.type === "text" ? p.text : "")).join(" ");
  const recent = messages.filter((m) => m.role === "user").slice(-2).map(userText).join(" ");

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: buildSystemPrompt(retrieve(notes, recent)),
    messages: await convertToModelMessages(messages),

    // These two settings turn the call into spans for OpikExporter (see
    // $lib/server/telemetry.ts). The chat id rides in runtimeContext and
    // becomes the Opik thread id, so each browser chat is one thread.
    runtimeContext: { threadId: id, traceName: "garden-chat-turn" },
    experimental_telemetry: {
      ...OpikExporter.getSettings({ name: "garden-chat-turn" }),
      includeRuntimeContext: { threadId: true, traceName: true },
    },
  });

  return result.toUIMessageStreamResponse();
}
