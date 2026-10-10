"""Optional OpenTelemetry instrumentation with zero-config no-op fallback."""
from __future__ import annotations

import contextlib
import os

try:
    from opentelemetry import trace
except ImportError:
    trace = None


@contextlib.contextmanager
def trace_phase(operation: str, **attributes):
    if trace is None or os.environ.get("SMARTAUTOMATION_TRACING_ENABLED", "").lower() != "true":
        yield
        return
    tracer = trace.get_tracer("smartautomation")
    with tracer.start_as_current_span(operation) as span:
        for key, value in attributes.items():
            if key in {"job_id", "phase", "state", "returncode"} and isinstance(value, (str, int, bool)):
                span.set_attribute(key, value)
        yield
