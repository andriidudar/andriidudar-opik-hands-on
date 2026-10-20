// Scripted demo: starts the SvelteKit dev server, plays three multi-turn
// conversations against /api/chat, prints the streamed replies, stops the server.
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { setTimeout as sleep } from "node:timers/promises";
import { config } from "dotenv";

config({ path: ".env", quiet: true });
config({ path: "../.env", quiet: true });

const PORT = process.env.DEMO_PORT ?? "5471";
const BASE = `http://localhost:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY (put it in .env or the repo-root .env).");
  process.exit(1);
}

const conversations = [
  {
    title: "Tomatoes with brown rings",
    turns: [
      "The lower leaves on my tomatoes have brown rings. What is going on?",
      "Should I water them more to help?",
    ],
  },
  {
    title: "A drooping monstera",
    turns: [
      "My monstera has yellow lower leaves. Am I overwatering it?",
      "How often should I water it then?",
    ],
  },
  {
    title: "Wandering off topic",
    turns: [
      "Which gardening gloves are best for roses?",
      "Never mind, can you recommend a good sci-fi novel instead?",
    ],
  },
];

console.log(`Starting the SvelteKit dev server on port ${PORT}...`);
const server = spawn("node_modules/.bin/vite", ["dev", "--port", PORT, "--strictPort"], {
  env: { ...process.env },
  stdio: ["ignore", "pipe", "pipe"],
  detached: true, // own process group, so the whole tree can be stopped
});
server.stdout.on("data", () => {});
server.stderr.on("data", (d) => process.stderr.write(d));
const exited = new Promise<void>((resolve) => server.once("exit", () => resolve()));

async function waitForServer(timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(BASE, { signal: AbortSignal.timeout(2000) })).ok) return;
    } catch {
      /* not up yet */
    }
    await sleep(500);
  }
  throw new Error("Dev server did not start in time");
}

// POST the full history like the Chat class does and print the SSE text deltas.
async function chatTurn(id: string, messages: unknown[]): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, messages }),
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  let text = "";
  let buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) {
          text += event.delta;
          process.stdout.write(event.delta);
        }
      } catch {
        /* ignore keep-alives */
      }
    }
  }
  process.stdout.write("\n");
  return text;
}

const message = (role: "user" | "assistant", text: string) => ({
  id: randomUUID(),
  role,
  parts: [{ type: "text", text }],
});

try {
  await waitForServer();
  for (const conversation of conversations) {
    const chatId = randomUUID(); // becomes the Opik thread id
    console.log(`\n=== ${conversation.title} (thread ${chatId.slice(0, 8)}) ===`);
    const history: ReturnType<typeof message>[] = [];
    for (const turn of conversation.turns) {
      console.log(`\nYou: ${turn}\nSprout: `);
      history.push(message("user", turn));
      history.push(message("assistant", await chatTurn(chatId, history)));
    }
  }
} finally {
  // SIGTERM runs the telemetry shutdown hook, which flushes pending spans to Opik.
  try {
    process.kill(-server.pid!, "SIGTERM");
  } catch {
    /* already gone */
  }
  await Promise.race([exited, sleep(10_000)]);
}
console.log("\nDone. Open the vercel-ai-sveltekit-garden-chat project in Opik.");
