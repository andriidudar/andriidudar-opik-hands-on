import asyncio

import pytest
from openinference.instrumentation.beeai import BeeAIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from aquarium.tools import read_tank_log
from aquarium.tracing import OpikShapingExporter, shape_for_opik


@pytest.fixture
def spans():
    memory = InMemorySpanExporter()
    provider = TracerProvider()
    # Shaping exporter in front of the in-memory one: what Opik would receive.
    provider.add_span_processor(SimpleSpanProcessor(OpikShapingExporter(memory)))
    instrumentor = BeeAIInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    yield memory
    instrumentor.uninstrument()


def test_traced_tool_call_still_works_and_is_shaped_as_a_tool_span(spans):
    # The instrumented tool is called for real (no model, no network, Opik not involved).
    async def call():
        return await read_tank_log.run({"tank_id": "jelly-4", "last_n": 1})

    out = asyncio.run(call())
    assert "moon jelly" in out.get_text_content()
    tool_spans = [s for s in spans.get_finished_spans() if s.attributes.get("openinference.span.kind") == "TOOL"]
    assert tool_spans, "expected a tool span"
    attrs = tool_spans[0].attributes
    assert "jelly-4" in attrs["gen_ai.tool.call.arguments"]
    assert "moon jelly" in attrs["gen_ai.tool.call.result"]


def test_shape_drops_token_spans_and_adds_provider():
    provider = TracerProvider()
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    tracer = provider.get_tracer("t")
    with tracer.start_as_current_span("new_token"):
        pass
    with tracer.start_as_current_span("OpenAIChatModel") as sp:
        sp.set_attribute("openinference.span.kind", "LLM")
        sp.set_attribute("llm.provider", "openai")
    token, llm = memory.get_finished_spans()
    assert shape_for_opik(token) is None
    assert shape_for_opik(llm).attributes["gen_ai.system"] == "openai"
