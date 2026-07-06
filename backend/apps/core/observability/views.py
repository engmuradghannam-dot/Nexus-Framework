"""
Prometheus metrics endpoint and health checks.
"""
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import redis
import time


def metrics_view(request):
    """Prometheus metrics scraping endpoint."""
    from django.http import HttpResponse
    return HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST
    )


def health_check(request):
    """Comprehensive health check endpoint."""
    checks = {
        'database': _check_database(),
        'cache': _check_cache(),
        'redis': _check_redis(),
    }

    all_healthy = all(c['status'] == 'healthy' for c in checks.values())

    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'timestamp': time.time(),
        'checks': checks,
    }, status=200 if all_healthy else 503)


def _check_database():
    try:
        connections['default'].cursor().execute('SELECT 1')
        return {'status': 'healthy', 'response_time_ms': 0}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def _check_cache():
    try:
        cache.set('health_check', 'ok', 1)
        value = cache.get('health_check')
        return {'status': 'healthy' if value == 'ok' else 'unhealthy'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def _check_redis():
    try:
        from django.conf import settings
        r = redis.from_url(getattr(settings, 'REDIS_URL', 'redis://redis:6379/0'))
        r.ping()
        info = r.info()
        return {
            'status': 'healthy',
            'used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
            'connected_clients': info.get('connected_clients', 0),
        }
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
