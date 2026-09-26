"""OpenTelemetry setup: traces, metrics and trace-correlated logs over OTLP/HTTP.

Built for the Grafana stack: one OTLP endpoint (Grafana Cloud's OTLP gateway, Alloy, or the
local ``grafana/otel-lgtm``) fans out to Tempo (traces), Mimir/Prometheus (metrics, PromQL)
and Loki (logs). Any other OTLP backend works the same way.

Call ``setup_telemetry()`` once per process (API: ``app.app``, worker: ``task_queue.task_broker``)
before creating the app/engine. Endpoint, auth headers and sampling come from the standard
``OTEL_EXPORTER_OTLP_*`` / ``OTEL_TRACES_SAMPLER*`` env vars; extra resource attributes from
``OTEL_RESOURCE_ATTRIBUTES``. A signal can be turned off with
``OTEL_{TRACES,METRICS,LOGS}_EXPORTER=none``. When disabled, the OTel API falls back to no-op
providers, so instrumented code costs nothing.
"""

import logging
import os
from importlib.metadata import PackageNotFoundError, version
from typing import Final

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import TelemetryConfig, load

_LOG_FORMAT: Final = (
    "%(asctime)s %(levelname)s [%(name)s] "
    "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(message)s"
)
_EXCLUDED_URLS: Final = "health,docs,openapi.json,redoc"

_configured = False


def _signal_enabled(signal: str) -> bool:
    return os.environ.get(f"OTEL_{signal}_EXPORTER", "otlp").strip().lower() != "none"


def _cfg() -> TelemetryConfig:
    return load("telemetry").telemetry


def _service_version() -> str:
    try:
        return version("backend-template")
    except PackageNotFoundError:
        return "unknown"


def _resource(cfg: TelemetryConfig) -> Resource:
    """Attributes Grafana uses to identify the service (``job``, env filters, App O11y).

    ``OTEL_RESOURCE_ATTRIBUTES`` is merged in by ``Resource.create`` and can add more.
    """
    attributes: dict[str, str] = {
        SERVICE_NAME: cfg.service_name,
        SERVICE_VERSION: _service_version(),
        DEPLOYMENT_ENVIRONMENT: load("app").app.environment,
    }
    if cfg.service_namespace:
        attributes[SERVICE_NAMESPACE] = cfg.service_namespace
    return Resource.create(attributes)


def setup_telemetry() -> None:
    """Configure logging and, if enabled, the global tracer and meter providers. Idempotent."""
    global _configured
    if _configured:
        return
    _configured = True

    cfg = _cfg()
    logging.basicConfig(level=cfg.log_level, format=_LOG_FORMAT, force=True)

    # Emit stable HTTP semantic conventions (http_server_request_duration_seconds, http_route,
    # http_response_status_code) which Grafana dashboards and App Observability expect,
    # instead of the legacy names. Must be set before any instrumentor initializes.
    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    if cfg.enabled:
        resource = _resource(cfg)

        tracer_provider = TracerProvider(resource=resource)
        if cfg.console_exporter:
            tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        elif _signal_enabled("TRACES"):
            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        if not cfg.console_exporter and _signal_enabled("METRICS"):
            reader = PeriodicExportingMetricReader(OTLPMetricExporter())
            metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

        if not cfg.console_exporter and _signal_enabled("LOGS"):
            logger_provider = LoggerProvider(resource=resource)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
            set_logger_provider(logger_provider)

    # Adds otelTraceID/otelSpanID to every record (for the stdout format above) and, when a
    # logger provider is configured, ships records over OTLP linked to the active span.
    LoggingInstrumentor().instrument(
        inject_trace_context=True,
        enable_log_auto_instrumentation=(
            cfg.enabled and not cfg.console_exporter and _signal_enabled("LOGS")
        ),
    )


def instrument_app(app: FastAPI) -> None:
    """Server spans and HTTP metrics for every request (replaces per-request logging)."""
    if _cfg().enabled:
        FastAPIInstrumentor.instrument_app(app, excluded_urls=_EXCLUDED_URLS)


def instrument_engine(engine: AsyncEngine) -> None:
    """A child span per SQL statement."""
    if _cfg().enabled:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def shutdown_telemetry() -> None:
    """Flush pending spans/metrics/logs. No-op for the default (no-op) providers."""
    from opentelemetry._logs import get_logger_provider

    providers = (trace.get_tracer_provider(), metrics.get_meter_provider(), get_logger_provider())
    for provider in providers:
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            shutdown()
