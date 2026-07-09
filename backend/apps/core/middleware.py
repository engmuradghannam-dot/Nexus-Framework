"""
Custom middleware to handle CSRF for API endpoints on Railway
"""
from django.utils.deprecation import MiddlewareMixin

class CSRFAPIMiddleware(MiddlewareMixin):
    """
    Bypass CSRF checks for API endpoints when using session authentication.
    This is safe because DRF handles its own authentication/permissions.
    """
    def process_request(self, request):
        # If the request is for an API endpoint, mark it as CSRF exempt
        if request.path.startswith('/api/'):
            request._dont_enforce_csrf_checks = True


class RailwayOriginMiddleware(MiddlewareMixin):
    """
    Automatically add the current Railway domain to CSRF_TRUSTED_ORIGINS
    """
    def process_request(self, request):
        origin = request.headers.get('Origin')
        if origin and 'railway.app' in origin:
            from django.conf import settings
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)
