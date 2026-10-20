// The only module that wires Opik in: builds VoltAgent's observability with an OTLP exporter aimed at Opik.
import { VoltAgentObservability } from "@voltagent/core";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { GenAIMappingExporter } from "./exporter.ts";

export const PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? "voltagent-meal-planner";

export function opikOtlpUrl(): string {
  const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");
  return `${base}/v1/private/otel/v1/traces`;
}

export function opikHeaders(): Record<string, string> {
  // `projectName` routes every span into one Opik project; Comet-Workspace picks the workspace.
  // Local Opik needs no Authorization header; Opik Cloud does.
  const headers: Record<string, string> = {
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
    projectName: PROJECT_NAME,
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  return headers;
}

export const observability = new VoltAgentObservability({
  serviceName: PROJECT_NAME,
  spanProcessors: [
    // The mapping exporter sits between VoltAgent's spans and the OTLP exporter: without it,
    // spans arrive but carry no token usage, provider or cost.
    new BatchSpanProcessor(new GenAIMappingExporter(new OTLPTraceExporter({ url: opikOtlpUrl(), headers: opikHeaders() }))),
  ],
});

// Call before exit: BatchSpanProcessor buffers, and unflushed spans never reach Opik.
export const flushTelemetry = () => observability.shutdown();
