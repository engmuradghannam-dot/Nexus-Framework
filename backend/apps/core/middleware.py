"""
ULTIMATE CSRF Fix - Completely disable CSRF for Railway deployment
"""
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class RailwayCsrfMiddleware(CsrfViewMiddleware):
    """
    Completely bypasses ALL CSRF checks for Railway deployment.
    This is a temporary fix until Railway domain is stable.
    """
    def process_request(self, request):
        # Log actual values for debugging
        origin = request.META.get('HTTP_ORIGIN', 'NOT_SET')
        host = request.META.get('HTTP_HOST', 'NOT_SET')
        x_forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST', 'NOT_SET')
        x_forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', 'NOT_SET')

        logger.info(f"CSRF Check - Origin: {origin}, Host: {host}, X-Forwarded-Host: {x_forwarded_host}, X-Forwarded-Proto: {x_forwarded_proto}")

        # COMPLETELY bypass CSRF for Railway
        if 'railway.app' in str(origin) or 'railway.app' in str(host) or 'railway.app' in str(x_forwarded_host):
            logger.info("Railway domain detected - bypassing CSRF")
            request.csrf_processing_done = True
            return None

        # Also bypass if no origin (same-origin request)
        if not origin or origin == 'NOT_SET':
            logger.info("No origin - bypassing CSRF")
            request.csrf_processing_done = True
            return None

        return super().process_request(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # If already marked as done, skip
        if getattr(request, 'csrf_processing_done', False):
            return None

        origin = request.META.get('HTTP_ORIGIN', '')
        host = request.META.get('HTTP_HOST', '')
        x_forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST', '')

        # Bypass for Railway
        if 'railway.app' in str(origin) or 'railway.app' in str(host) or 'railway.app' in str(x_forwarded_host):
            logger.info("Railway domain detected in process_view - bypassing CSRF")
            request.csrf_processing_done = True
            return None

        # Bypass if no origin
        if not origin:
            request.csrf_processing_done = True
            return None

        return super().process_view(request, callback, callback_args, callback_kwargs)


class CSRFAPIMiddleware(MiddlewareMixin):
    """Bypass CSRF for API endpoints"""
    def process_request(self, request):
        if request.path.startswith('/api/'):
            request._dont_enforce_csrf_checks = True
