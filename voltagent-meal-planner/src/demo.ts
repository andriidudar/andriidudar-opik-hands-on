// Runs three scripted planning requests through the meal-planner agent.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});
// Always talk to the public OpenAI API, not a local proxy from the build machine.
delete process.env.OPENAI_BASE_URL;

// VoltAgent puts the system prompt inside the messages array; the AI SDK warns about that on every call.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { VoltAgent } = await import("@voltagent/core");
const { mealPlanner } = await import("./agent.ts");
// Imported after dotenv so the exporter sees OPIK_* variables when it initializes.
const { observability, flushTelemetry, PROJECT_NAME } = await import("./telemetry/setup.ts");

// Passing `observability` makes VoltAgent emit its OTel spans through the Opik exporter; no server option keeps this a script.
new VoltAgent({ agents: { mealPlanner }, observability });

const REQUESTS = [
  "Which vegan recipes can I cook this week with at most one missing ingredient?",
  "Plan three quick dinners (20 minutes or less) and give me one combined shopping list.",
  "Do I have enough eggs and parmesan for carbonara, and what would I still need to buy?",
];

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===\nYou:     ${request}`);
  const result = await mealPlanner.generateText(request);
  console.log(`Planner: ${result.text}`);
}
// Flush buffered spans so the final request reaches Opik before the process exits.
await flushTelemetry();
console.log(`\nDone. Open the "${PROJECT_NAME}" project in Opik to see the traces.`);
process.exit(0);
