// The whole Opik integration lives here: an OpenTelemetry SDK whose trace
// exporter is OpikExporter, plus the AI SDK's own telemetry integration.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";
import "./env";

export const OPIK_PROJECT = "vercel-ai-sveltekit-garden-chat";

// OpikExporter turns each finished AI SDK span tree into an Opik trace with
// its spans. The pinned Opik client sends everything to one project; the URL,
// workspace and (for Cloud) API key come from OPIK_* environment variables.
const exporter = new OpikExporter({
  client: new Opik({ projectName: OPIK_PROJECT }),
  tags: ["sveltekit", "streaming"],
});

// The default batch processor waits 5 s before exporting, so a short-lived
// server (like the one npm run demo starts) was stopped with the last turns
// still queued and they never reached Opik. A 500 ms delay still sends all
// spans of one chat turn together, which keeps each turn to one trace update.
const sdk = new NodeSDK({
  serviceName: OPIK_PROJECT,
  spanProcessors: [new BatchSpanProcessor(exporter, { scheduledDelayMillis: 500 })],
});
sdk.start();

// AI SDK v7 emits spans through a registered telemetry integration, so this
// registration is what feeds the exporter above. enrichSpan copies the
// threadId (and trace name) from runtimeContext onto the span; the threadId is
// how Opik groups the turns of one chat into a single thread.
registerTelemetry(
  new OpenTelemetry({
    usage: true, // token counts on the llm span, so Opik can compute cost
    enrichSpan: ({ runtimeContext }) => {
      const attributes: Record<string, string> = {};
      if (runtimeContext?.threadId != null) {
        attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
      }
      if (runtimeContext?.traceName != null) {
        attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
      }
      return attributes;
    },
  }),
);
