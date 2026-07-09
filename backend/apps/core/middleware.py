"""
Railway-safe CSRF Middleware
Handles CSRF for Railway deployment and local development gracefully.
"""
from django.utils.deprecation import MiddlewareMixin


class RailwayCsrfMiddleware(MiddlewareMixin):
    """
    Custom CSRF middleware that handles Railway deployment
    and local development gracefully.
    """
    def process_request(self, request):
        # Skip CSRF for API endpoints
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
