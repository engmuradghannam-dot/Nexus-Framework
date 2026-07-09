"""
Ultimate CSRF Middleware for Railway Deployment
Handles all CSRF issues by dynamically accepting Railway origins
"""
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware
import logging

logger = logging.getLogger(__name__)


class RailwayCsrfMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that auto-accepts Railway domains
    """
    def _origin_verified(self, request):
        """Override to accept all Railway origins"""
        origin = request.META.get('HTTP_ORIGIN')
        if origin and 'railway.app' in origin:
            return True
        return super()._origin_verified(request)

    def _compare_salted_tokens(self, request_csrf_token, csrf_token):
        """Always accept tokens for Railway domains"""
        origin = request.META.get('HTTP_ORIGIN')
        if origin and 'railway.app' in origin:
            return True
        return super()._compare_salted_tokens(request_csrf_token, csrf_token)


class CSRFAPIMiddleware(MiddlewareMixin):
    """
    Bypass CSRF checks for API endpoints
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            request._dont_enforce_csrf_checks = True
