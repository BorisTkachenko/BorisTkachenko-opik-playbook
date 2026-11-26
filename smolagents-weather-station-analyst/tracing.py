"""Send smolagents spans to Opik over OpenTelemetry."""

import os

PROJECT_NAME = "smolagents-weather-station-analyst"


def setup_tracing():
    """Instrument smolagents and export its spans to Opik's OTLP endpoint.

    Returns the TracerProvider so the caller can flush it before exiting.
    """
    # Opik's OTLP endpoint reads the workspace and project from headers. The
    # projectName header is what keeps traces out of "Default Project";
    # locally no Authorization header is needed (Opik Cloud wants your API key there).
    os.environ.setdefault(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:5173/api/v1/private/otel"
    )
    os.environ.setdefault(
        "OTEL_EXPORTER_OTLP_HEADERS",
        f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')},projectName={PROJECT_NAME}",
    )

    from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    # The exporter reads the endpoint and headers above; every finished span is POSTed to Opik.
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    # SmolagentsInstrumentor patches smolagents: each agent run, step, model call and
    # code execution becomes a span, with the generated code and execution logs as attributes.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider
