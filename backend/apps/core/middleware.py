"""
Ultimate CSRF Middleware for Railway Deployment
Completely bypasses CSRF for Railway domains
"""
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin


class RailwayCsrfMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that completely bypasses CSRF for Railway domains.
    """
    def process_request(self, request):
        # Completely skip CSRF processing for Railway domains
        origin = request.META.get('HTTP_ORIGIN', '')
        host = request.META.get('HTTP_HOST', '')

        if 'railway.app' in origin or 'railway.app' in host:
            # Mark as CSRF exempt - Django will skip CSRF checks
            request.csrf_processing_done = True
            return None

        # For non-Railway domains, use normal CSRF processing
        return super().process_request(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Also skip in process_view for Railway
        origin = request.META.get('HTTP_ORIGIN', '')
        host = request.META.get('HTTP_HOST', '')

        if 'railway.app' in origin or 'railway.app' in host:
            return None

        return super().process_view(request, callback, callback_args, callback_kwargs)


class CSRFAPIMiddleware(MiddlewareMixin):
    """
    Bypass CSRF checks for API endpoints
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            request._dont_enforce_csrf_checks = True
