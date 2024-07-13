import logging

from fastapi import FastAPI
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ConcurrentMultiSpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.base import BaseHTTPMiddleware

from thermostatter_api import PROJECT_NAME
from thermostatter_api.logger import LOGGER

# Service name is required for most backends
resource = Resource(attributes={SERVICE_NAME: PROJECT_NAME})

trace_provider = TracerProvider(
    resource=resource, active_span_processor=ConcurrentMultiSpanProcessor()
)
processor = BatchSpanProcessor(OTLPSpanExporter())
trace_provider.add_span_processor(processor)
trace.set_tracer_provider(trace_provider)

reader = PeriodicExportingMetricReader(OTLPMetricExporter())
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)

logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
_logs.set_logger_provider(logger_provider)
logger_handler = LoggingHandler(logger_provider=logger_provider, level=logging.INFO)
LOGGER.addHandler(logger_handler)


def get_current_trace_id():
    trace_id = trace.get_current_span().get_span_context().trace_id
    return trace.format_trace_id(trace_id)


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = get_current_trace_id()
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        return response


def setup_telemetry(app: FastAPI):
    app.add_middleware(TraceIDMiddleware)
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=trace_provider, meter_provider=meter_provider
    )


def shutdown_telemetry():
    trace_provider.shutdown()
    logger_provider.shutdown()
    meter_provider.shutdown()
