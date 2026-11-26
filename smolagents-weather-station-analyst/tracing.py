"""Send smolagents spans to Opik over OpenTelemetry."""

import os
from collections.abc import Sequence

PROJECT_NAME = "smolagents-weather-station-analyst"
PROVIDER = "openai"  # the model client in agent.py is OpenAIServerModel


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
    # OpikFriendlyExporter patches two attribute problems on the way out (see its docstring).
    provider.add_span_processor(SimpleSpanProcessor(OpikFriendlyExporter(OTLPSpanExporter())))
    # SmolagentsInstrumentor patches smolagents: each agent run, step, model call and
    # code execution becomes a span, with the generated code and execution logs as attributes.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider


def fix_attributes(attrs: dict) -> dict:
    """Return the attributes Opik should see for one span.

    * Opik turns ANY span with `llm.token_count.*` into an `llm` span with usage.
      OpenInference also stamps the agent-run span with its summed token counts, so the
      trace total double-counted every token. Only spans that name a model keep them.
    * Opik prices a span only when it knows the provider and model. OpenInference sends
      the model name but Opik reads the provider from `gen_ai.system`, so add it.
    """
    out = dict(attrs)
    if "llm.model_name" in out:
        out.setdefault("gen_ai.system", PROVIDER)
    else:
        for key in [k for k in out if k.startswith("llm.token_count.")]:
            del out[key]
    return out


class OpikFriendlyExporter:
    """Wraps the OTLP exporter and rewrites span attributes with `fix_attributes`.

    Spans are immutable once ended, so each one is rebuilt as a copy before export.
    """

    def __init__(self, inner):
        self._inner = inner

    def export(self, spans: Sequence):
        from opentelemetry.sdk.trace import ReadableSpan

        fixed = [
            ReadableSpan(
                name=s.name,
                context=s.context,
                parent=s.parent,
                resource=s.resource,
                attributes=fix_attributes(dict(s.attributes or {})),
                events=s.events,
                links=s.links,
                kind=s.kind,
                instrumentation_scope=s.instrumentation_scope,
                status=s.status,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in spans
        ]
        return self._inner.export(fixed)

    def shutdown(self):
        return self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000):
        return self._inner.force_flush(timeout_millis)
