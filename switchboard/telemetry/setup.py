from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, cast

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass
class TelemetryController:
    tracer_provider: TracerProvider
    span_processor: BatchSpanProcessor
    span_exporter: OTLPSpanExporter
    meter_provider: MeterProvider
    metric_exporter: OTLPMetricExporter

    def shutdown(self) -> None:
        """Flush and shut down telemetry exporters."""
        cast(Any, self.span_processor).shutdown()
        cast(Any, self.span_exporter).shutdown()
        cast(Any, self.meter_provider).shutdown()
        cast(Any, self.metric_exporter).shutdown()
        cast(Any, self.tracer_provider).shutdown()


def _telemetry_enabled() -> bool:
    flag = os.getenv("SWITCHBOARD_ENABLE_TELEMETRY")
    if flag is None:
        return False
    return flag.lower() in _TRUTHY


def configure_telemetry(service_name: str = "switchboard-api") -> TelemetryController | None:
    if os.getenv("OTEL_SDK_DISABLED", "").lower() in _TRUTHY:
        return None
    if not _telemetry_enabled():
        return None

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    resource = Resource(attributes={"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
    metrics.set_meter_provider(meter_provider)

    return TelemetryController(
        tracer_provider=tracer_provider,
        span_processor=span_processor,
        span_exporter=span_exporter,
        meter_provider=meter_provider,
        metric_exporter=metric_exporter,
    )
