// Mastra instance with Opik observability. Mastra's Observability layer records
// each agent run as a span tree, and OtelExporter ships it to Opik's OTLP
// endpoint, where it becomes one trace per agent.generate() call.
import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { bankingAgent } from "./agent.ts";

export const OPIK_PROJECT = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";

// Headers Opik's OTLP endpoint reads. Local Opik needs no Authorization;
// Opik Cloud wants the API key there.
export function opikHeaders(env: NodeJS.ProcessEnv = process.env): Record<string, string> {
  const headers: Record<string, string> = {
    "Comet-Workspace": env.OPIK_WORKSPACE ?? "default",
    // projectName routes every trace into this Opik project; without it traces
    // land in "Default Project".
    projectName: env.OPIK_PROJECT_NAME ?? "mastra-banking-agent",
  };
  if (env.OPIK_API_KEY) headers.Authorization = env.OPIK_API_KEY;
  return headers;
}

// OPIK_URL_OVERRIDE is the REST base (http://localhost:5173/api/); the OTLP
// ingest path hangs off it.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");

// OPIK_TRACK_DISABLE=true skips the exporter entirely: the agent still runs,
// nothing is sent to Opik. The offline tests rely on this.
const tracking = process.env.OPIK_TRACK_DISABLE !== "true";

export const mastra = new Mastra({
  agents: { bankingAgent },
  ...(tracking && {
    observability: new Observability({
      configs: {
        default: {
          serviceName: OPIK_PROJECT,
          exporters: [
            new OtelExporter({
              provider: {
                custom: { endpoint: `${opikBase}/v1/private/otel/v1/traces`, protocol: "http/json", headers: opikHeaders() },
              },
            }),
          ],
        },
      },
    }),
  }),
});
