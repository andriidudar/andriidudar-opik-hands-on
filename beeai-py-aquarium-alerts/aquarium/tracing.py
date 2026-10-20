"""Opik tracing for BeeAI over plain OpenTelemetry: no Opik SDK call in the agent code."""
import os

from openinference.instrumentation.beeai import BeeAIInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

PROJECT = "beeai-py-aquarium-alerts"
# Local self-hosted Opik. For Opik Cloud use https://www.comet.com/opik/api/v1/private/otel
# plus an Authorization header carrying your API key.
OTLP_BASE = os.environ.get("OPIK_OTEL_ENDPOINT", "http://localhost:5173/api/v1/private/otel")

_provider: TracerProvider | None = None


def shape_for_opik(span: ReadableSpan) -> ReadableSpan | None:
    """Return the span as Opik wants to see it, or None to drop it.

    - BeeAI emits one `new_token` span per streamed token (hundreds per alert); they bury the real steps.
    - OpenInference carries the model and token counts but no `gen_ai.system`, which Opik reads as the
      provider; without it the llm span has usage but no estimated cost.
    - Tool spans only become Opik `tool` spans when they carry `gen_ai.tool.call.*` attributes.
    """
    if span.name == "new_token":
        return None
    attrs = dict(span.attributes or {})
    kind = attrs.get("openinference.span.kind")
    if kind == "LLM" and "llm.provider" in attrs:
        attrs["gen_ai.system"] = attrs["llm.provider"]
    elif kind == "TOOL":
        attrs["gen_ai.tool.call.arguments"] = attrs.get("input.value", "")
        attrs["gen_ai.tool.call.result"] = attrs.get("output.value", "")
    else:
        return span
    return ReadableSpan(
        name=span.name, context=span.context, parent=span.parent, resource=span.resource,
        attributes=attrs, events=span.events, links=span.links, kind=span.kind, status=span.status,
        start_time=span.start_time, end_time=span.end_time, instrumentation_scope=span.instrumentation_scope,
    )


class OpikShapingExporter(SpanExporter):
    """Wraps the OTLP exporter and applies shape_for_opik to every span on its way out."""

    def __init__(self, inner: SpanExporter) -> None:
        self._inner = inner

    def export(self, spans):
        shaped = [x for x in (shape_for_opik(s) for s in spans) if x is not None]
        return self._inner.export(shaped) if shaped else SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._inner.force_flush(timeout_millis)


def setup_tracing() -> None:
    """Ship every BeeAI span to Opik. Call once, before any agent is built."""
    global _provider
    # The `projectName` header routes spans to this Opik project (otherwise they land in "Default Project");
    # `Comet-Workspace` picks the workspace.
    exporter = OTLPSpanExporter(
        endpoint=f"{OTLP_BASE}/v1/traces",
        headers={"projectName": PROJECT, "Comet-Workspace": os.environ.get("OPIK_WORKSPACE", "default")},
    )
    _provider = TracerProvider()
    _provider.add_span_processor(BatchSpanProcessor(OpikShapingExporter(exporter)))
    trace.set_tracer_provider(_provider)
    # OpenInference turns BeeAI's event emitter into spans: one agent span per run, one per ReAct
    # iteration, an LLM span per model call (with token counts) and a tool span per tool call.
    BeeAIInstrumentor().instrument()


def flush_tracing() -> None:
    """Export whatever the batch processor still holds; without it a short script exits and drops its last spans."""
    if _provider is not None:
        _provider.force_flush()
