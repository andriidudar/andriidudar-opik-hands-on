"""Send Pydantic AI's OpenTelemetry spans to Opik's OTLP endpoint through logfire."""

import os

import logfire
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

PROJECT_NAME = "pydantic-ai-calendar-extraction"
# Local self-hosted Opik. For Opik Cloud use https://www.comet.com/opik/api/v1/private/otel
# and add an Authorization=<api key> header.
OTLP_ENDPOINT = os.getenv("OPIK_OTEL_ENDPOINT", "http://localhost:5173/api/v1/private/otel/v1/traces")


def setup_tracing() -> None:
    # The projectName header decides which Opik project receives the traces;
    # without it everything lands in "Default Project". Comet-Workspace picks the workspace.
    exporter = OTLPSpanExporter(
        endpoint=OTLP_ENDPOINT,
        headers={"Comet-Workspace": os.getenv("OPIK_WORKSPACE", "default"), "projectName": PROJECT_NAME},
    )
    # logfire is only the OTel bridge here: send_to_logfire=False keeps data local, and the
    # extra span processor ships every span to Opik's OTLP ingest.
    logfire.configure(
        send_to_logfire=False,
        console=False,  # keep the terminal for results; spans go to Opik
        service_name=PROJECT_NAME,
        additional_span_processors=[BatchSpanProcessor(exporter)],
    )
    # Makes every Agent run emit gen_ai spans: invoke_agent (the trace root) and one
    # llm span per model call, with token usage, which Opik renders as a trace tree.
    logfire.instrument_pydantic_ai()


def flush_tracing() -> None:
    # BatchSpanProcessor buffers spans; without this flush a short CLI run can exit
    # before they are sent and the project stays empty.
    logfire.force_flush()
