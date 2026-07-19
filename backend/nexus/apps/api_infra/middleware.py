import time
import json
from django.utils.deprecation import MiddlewareMixin
from .models import APIRequestLog

class APIRequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, '_start_time') and request.path.startswith('/api/'):
            duration = int((time.time() - request._start_time) * 1000)

            try:
                body = json.loads(request.body) if request.body else {}
            except:
                body = {}

            try:
                response_body = json.loads(response.content) if response.content else {}
            except:
                response_body = {}

            APIRequestLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                method=request.method,
                path=request.path,
                query_params=dict(request.GET),
                request_body=body,
                response_status=response.status_code,
                response_body=response_body,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                duration_ms=duration
            )
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
