"""Send Pydantic AI's OpenTelemetry spans to Opik's OTLP endpoint."""

import os

PROJECT_NAME = "pydantic-ai-camera-listing-extraction"


def setup_tracing() -> None:
    # Offline tests set OPIK_TRACK_DISABLE=true; skip the OTLP exporter too so nothing tries to reach Opik.
    if os.getenv("OPIK_TRACK_DISABLE", "").lower() in ("1", "true", "yes"):
        return
    # Opik ingests OTLP at <api base>/v1/private/otel. The Comet-Workspace header picks
    # the workspace; projectName makes spans land in this example's project, not "Default Project".
    base = os.getenv("OPIK_URL_OVERRIDE", "http://localhost:5173/api/").rstrip("/")
    headers = f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')},projectName={PROJECT_NAME}"
    if os.getenv("OPIK_API_KEY"):  # only Opik Cloud needs a key; local self-hosted sends none
        headers = f"Authorization={os.environ['OPIK_API_KEY']},{headers}"
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", f"{base}/v1/private/otel")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_HEADERS", headers)
    os.environ["OTEL_METRICS_EXPORTER"] = "none"

    import logfire
    # OpikSpanProcessor attaches the agent's OTel spans to the surrounding @opik.track trace,
    # so one extraction = one trace. Without it they arrive as separate, unrelated traces.
    from opik.integrations.otel import OpikSpanProcessor

    # send_to_logfire=False keeps everything local to Opik; the OTLP env vars above feed the exporter.
    logfire.configure(send_to_logfire=False, console=False, additional_span_processors=[OpikSpanProcessor()])
    # Emits invoke_agent / chat <model> / running tool spans with gen_ai token usage attributes.
    logfire.instrument_pydantic_ai()
