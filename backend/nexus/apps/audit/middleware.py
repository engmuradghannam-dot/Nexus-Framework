from .signals import set_current_audit_user


class AuditUserMiddleware:
    """Makes request.user available to the audit signal handlers, which run
    outside of request scope, via a contextvar."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_audit_user(getattr(request, 'user', None))
        try:
            return self.get_response(request)
        finally:
            set_current_audit_user(None)
