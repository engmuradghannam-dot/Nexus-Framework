"""Liveness/readiness probe for load balancers, container orchestrators,
and uptime monitoring - standard in any enterprise deployment. Unauthenticated
by design (a health check gated behind login can't be polled by
infrastructure that isn't itself logged in), and deliberately does not leak
anything beyond up/down status per dependency."""
from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    checks = {}

    try:
        connections['default'].cursor().execute('SELECT 1')
        checks['database'] = 'ok'
    except OperationalError:
        checks['database'] = 'unreachable'

    try:
        cache.set('health_check', '1', timeout=5)
        checks['cache'] = 'ok' if cache.get('health_check') == '1' else 'unreachable'
    except Exception:
        checks['cache'] = 'unreachable'

    healthy = all(v == 'ok' for v in checks.values())
    return Response({'status': 'healthy' if healthy else 'unhealthy', 'checks': checks},
                     status=200 if healthy else 503)
