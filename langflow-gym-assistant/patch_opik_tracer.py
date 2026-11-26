"""Build-time patch for Langflow 1.13.4's Opik tracer (see README, "Gotchas").

Langflow ends each component span with `self._client.span(**span.__dict__)`. The span
object carries fields (`source`, and since opik 2.1 `environment`) that `Opik.span()`
does not accept, so every component span raises a TypeError and is dropped. This rewrites
that one call to pass only the keyword arguments `Opik.span()` accepts. It fails the
build if the line is not found, so a Langflow upgrade that changes it is noticed.
"""

import importlib.util
from pathlib import Path

ORIGINAL = "self._client.span(**span.__dict__)"
PATCHED = (
    "self._client.span(**{k: v for k, v in span.__dict__.items() "
    "if k in __import__('inspect').signature(self._client.span).parameters})"
)

path = Path(importlib.util.find_spec("langflow.services.tracing.opik").origin)
source = path.read_text()
if source.count(ORIGINAL) != 1:
    raise SystemExit(f"expected exactly one `{ORIGINAL}` in {path}; Langflow changed, re-check the patch")
path.write_text(source.replace(ORIGINAL, PATCHED))
print(f"patched {path}")
