from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tracing import OpikFriendlyExporter, fix_attributes


def test_model_spans_gain_a_provider_and_keep_tokens():
    out = fix_attributes({"llm.model_name": "gpt-4o-mini", "llm.token_count.prompt": 10})
    assert out["gen_ai.system"] == "openai" and out["llm.token_count.prompt"] == 10


def test_agent_spans_lose_summed_token_counts():
    out = fix_attributes({"llm.token_count.prompt": 10, "llm.token_count.total": 12, "x": 1})
    assert out == {"x": 1}


def test_exporter_rewrites_spans_before_export():
    sink = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(OpikFriendlyExporter(sink)))
    with provider.get_tracer("t").start_as_current_span("agent") as span:
        span.set_attribute("llm.token_count.total", 5)
    with provider.get_tracer("t").start_as_current_span("model") as span:
        span.set_attribute("llm.model_name", "gpt-4o-mini")
    agent, model = sink.get_finished_spans()
    assert "llm.token_count.total" not in agent.attributes
    assert model.attributes["gen_ai.system"] == "openai"
