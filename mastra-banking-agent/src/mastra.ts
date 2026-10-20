// Mastra instance with Opik observability. Mastra's Observability layer records
// each agent run as a span tree, and OtelExporter ships it to Opik's OTLP
// endpoint, where it becomes one trace per agent.generate() call.
import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { bankingAgent } from "./agent.ts";

export const OPIK_PROJECT = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";

// OPIK_URL_OVERRIDE is the REST base (http://localhost:5173/api/); the OTLP
// ingest path hangs off it.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");

// Local Opik needs no Authorization header; Opik Cloud wants the API key there.
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  // projectName routes every trace into this Opik project (default otherwise).
  projectName: OPIK_PROJECT,
};
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

export const mastra = new Mastra({
  agents: { bankingAgent },
  observability: new Observability({
    configs: {
      default: {
        serviceName: OPIK_PROJECT,
        exporters: [
          new OtelExporter({
            provider: {
              custom: { endpoint: `${opikBase}/v1/private/otel/v1/traces`, protocol: "http/json", headers },
            },
          }),
        ],
      },
    },
  }),
});
