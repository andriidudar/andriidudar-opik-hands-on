// Runs three scripted customer requests through the banking agent: `npm run demo`.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Load the example's .env first, then the repo-root .env.
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { mastra } = await import("./mastra.ts");

const REQUESTS = [
  "What's my checking balance on CHK-2210, and how much is in savings?",
  "Show me the last 4 transactions on CHK-9054. Anything look odd?",
  "Two charges of $249 from Unknown Merchant 88213 on CHK-9054 are not mine. Please freeze that card.",
];

const agent = mastra.getAgent("bankingAgent");

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Customer: ${request}`);
  const result = await agent.generate(request, { maxSteps: 6 });
  console.log(`Agent:    ${result.text}`);
}
