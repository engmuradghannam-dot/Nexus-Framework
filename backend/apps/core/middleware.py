"""
ULTIMATE CSRF DISABLE - For Railway Deployment Only
This completely disables CSRF protection. Use with caution.
"""
from django.utils.deprecation import MiddlewareMixin


class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Completely disables CSRF checks for ALL requests.
    This is a temporary fix for Railway deployment issues.
    """
    def process_request(self, request):
        # Mark CSRF as already processed - Django will skip all CSRF checks
        request.csrf_processing_done = True
