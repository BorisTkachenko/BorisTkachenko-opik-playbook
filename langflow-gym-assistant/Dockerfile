# Langflow 1.13.4 with one fix to its built-in Opik tracer: without it, every
# component span (Chat Input, Message History, Prompt, Chat Output) fails with
# "Opik.span() got an unexpected keyword argument 'source'" and never reaches Opik.
FROM langflowai/langflow:1.13.4

COPY patch_opik_tracer.py /tmp/patch_opik_tracer.py
RUN /app/.venv/bin/python /tmp/patch_opik_tracer.py
