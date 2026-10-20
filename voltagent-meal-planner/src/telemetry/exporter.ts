// A SpanExporter decorator: renames attributes, then hands spans to the real OTLP exporter.
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { mapVoltAgentAttributes, type Attrs } from "./genai-mapper.ts";

export class GenAIMappingExporter implements SpanExporter {
  constructor(private readonly inner: SpanExporter) {}

  export(spans: ReadableSpan[], done: Parameters<SpanExporter["export"]>[1]): void {
    // Spans are mutated just before export, so Opik sees gen_ai.* keys and VoltAgent's own code is untouched.
    for (const span of spans) mapVoltAgentAttributes(span.attributes as Attrs);
    this.inner.export(spans, done);
  }
  shutdown(): Promise<void> {
    return this.inner.shutdown();
  }
  forceFlush(): Promise<void> {
    return this.inner.forceFlush?.() ?? Promise.resolve();
  }
}
