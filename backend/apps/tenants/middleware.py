"""Set the current tenant for each request, for database routing.

The tenant comes from the authenticated user's tenant link. It's set at the
start of the request and cleared at the end, so a pooled worker thread never
leaks one request's tenant into the next.
"""
from .routing import clear_current_tenant, set_current_tenant


class CurrentTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            tenant = getattr(user, "tenant", None)
        set_current_tenant(tenant)
        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()  # never leak across pooled requests
        return response
