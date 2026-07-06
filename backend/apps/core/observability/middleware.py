"""
OpenTelemetry middleware for distributed tracing.
Captures every request with spans, metrics, and logs.
"""
import time
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from django.conf import settings


class ObservabilityMiddleware:
    """
    Middleware that captures:
    - Request/response metrics (latency, status code, endpoint)
    - Distributed tracing spans
    - Structured logging
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Initialize OpenTelemetry tracer
        resource = Resource(attributes={
            SERVICE_NAME: "nexus-erp-backend"
        })
        provider = TracerProvider(resource=resource)

        # OTLP exporter to Tempo/Jaeger
        otlp_exporter = OTLPSpanExporter(
            endpoint=getattr(settings, 'OTEL_EXPORTER_OTLP_ENDPOINT', 'http://tempo:4317'),
            insecure=True
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(__name__)

    def __call__(self, request):
        start_time = time.time()

        # Extract tenant info for tracing
        tenant_id = getattr(request, 'tenant', {}).get('id', 'unknown') if hasattr(request, 'tenant') else 'unknown'
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'

        with self.tracer.start_as_current_span(
            f"{request.method} {request.path}",
            attributes={
                "http.method": request.method,
                "http.url": request.build_absolute_uri(),
                "http.target": request.path,
                "tenant.id": str(tenant_id),
                "user.id": str(user_id),
            }
        ) as span:
            response = self.get_response(request)

            duration = time.time() - start_time

            # Add response attributes to span
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.duration_ms", duration * 1000)

            # Log structured metrics
            self._log_request(request, response, duration, tenant_id)

            return response

    def _log_request(self, request, response, duration, tenant_id):
        """Structured logging for Loki/Promtail ingestion."""
        import logging
        logger = logging.getLogger('nexus.observability')

        logger.info(
            "HTTP Request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "tenant_id": str(tenant_id),
                "user_agent": request.META.get('HTTP_USER_AGENT', ''),
                "remote_addr": self._get_client_ip(request),
            }
        )

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class MetricsMiddleware:
    """
    Prometheus metrics middleware.
    Exposes counters and histograms for all requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        from prometheus_client import Counter, Histogram, Info

        # Request metrics
        self.request_count = Counter(
            'django_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'tenant']
        )

        self.request_latency = Histogram(
            'django_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0]
        )

        self.request_size = Histogram(
            'django_http_request_size_bytes',
            'HTTP request size',
            ['method', 'endpoint']
        )

        self.response_size = Histogram(
            'django_http_response_size_bytes',
            'HTTP response size',
            ['method', 'endpoint']
        )

        # Application info
        self.app_info = Info('nexus_erp', 'Nexus ERP application info')
        self.app_info.info({'version': '2.0.0', 'environment': getattr(settings, 'ENVIRONMENT', 'development')})

    def __call__(self, request):
        import time
        start_time = time.time()

        tenant = getattr(request, 'tenant', {}).get('schema_name', 'public') if hasattr(request, 'tenant') else 'public'
        endpoint = request.resolver_match.route if hasattr(request, 'resolver_match') and request.resolver_match else request.path

        response = self.get_response(request)

        duration = time.time() - start_time
        status = str(response.status_code)

        # Record metrics
        self.request_count.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status,
            tenant=tenant
        ).inc()

        self.request_latency.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        if request.content_length:
            self.request_size.labels(method=request.method, endpoint=endpoint).observe(request.content_length)

        if hasattr(response, 'content'):
            self.response_size.labels(method=request.method, endpoint=endpoint).observe(len(response.content))

        return response
