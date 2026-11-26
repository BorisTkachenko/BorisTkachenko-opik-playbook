# n8n plus the n8n-observability hooks.
# n8n loads every file listed in EXTERNAL_HOOK_FILES at startup. The hooks in
# n8n-observability open an OpenTelemetry span for each workflow execution and
# one child span per node, then export them over OTLP. Point OTLP at Opik and
# every run of every workflow becomes an Opik trace — no node or code changes.
FROM n8nio/n8n:2.41.7

USER root
RUN npm install -g n8n-observability@1.0.3

ENV EXTERNAL_HOOK_FILES=/usr/local/lib/node_modules/n8n-observability/dist/hooks.cjs

USER node
