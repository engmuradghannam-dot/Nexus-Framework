"""
Structured logging configuration for Loki ingestion.
"""
import logging
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for Loki log ingestion."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, 'tenant_id'):
            log_data['tenant_id'] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id

        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class TenantAwareFilter(logging.Filter):
    """Add tenant context to all log records."""

    def filter(self, record):
        from apps.core.threadlocal import get_current_tenant
        tenant = get_current_tenant()
        record.tenant_id = str(tenant.get('id')) if tenant else 'system'
        return True


def configure_logging():
    """Configure structured logging for the application."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'filters': {
            'tenant_aware': {
                '()': TenantAwareFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'filters': ['tenant_aware'],
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/app/logs/nexus.json',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
                'filters': ['tenant_aware'],
            },
            'promtail': {
                'class': 'logging.handlers.SysLogHandler',
                'address': ('loki', 1514),
                'formatter': 'json',
            },
        },
        'loggers': {
            'nexus': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'nexus.observability': {
                'handlers': ['console', 'file', 'promtail'],
                'level': 'INFO',
                'propagate': False,
            },
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
            },
        },
    }
