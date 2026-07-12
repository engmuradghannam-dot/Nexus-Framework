"""Nexus Framework URL Configuration"""

import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import include, path, re_path

from nexus import pwa
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.admin_site import admin_site


def spa_index(request):
    """Serve the built React SPA entry point for non-API routes."""
    index_path = os.path.join(settings.STATIC_ROOT, "index.html")
    try:
        with open(index_path, "rb") as f:
            return HttpResponse(f.read(), content_type="text/html")
    except FileNotFoundError:
        raise Http404("Frontend build not found.")


urlpatterns = [
    path("sw.js", pwa.service_worker),
    path("manifest.webmanifest", pwa.manifest),
    path("admin/", admin_site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/core/", include("apps.core.urls")),
    path("api/pmo/", include("apps.pmo.urls")),
    path("api/industry/", include("apps.industry.urls")),
    path("api/ai/", include("apps.ai_module.urls")),
    path("api/regulatory/", include("apps.regulatory.urls")),
    path("api/hr/", include("apps.hr.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/manufacturing/", include("apps.manufacturing.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/assets/", include("apps.assets.urls")),
    path("api/buying/", include("apps.buying.urls")),
    path("api/selling/", include("apps.selling.urls")),
    path("api/crm/", include("apps.crm.urls")),
    path("api/taxes/", include("apps.taxes.urls")),
    path("api/i18n/", include("apps.i18n.urls")),

    path("api/controls/", include("apps.controls.urls")),
    path("api/", include("apps.records.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/invoicing/", include("apps.invoicing.urls")),
    path("api/rbac/", include("apps.rbac.urls")),
    path("api/hr/", include("apps.attendance.urls")),
    path("api/security/", include("apps.twofa.urls")),
    path("api/stock/", include("apps.stockledger.urls")),
    path("api/trade/", include("apps.trade.urls")),
    path("api/depreciation/", include("apps.depreciation.urls")),
    path("api/banking/", include("apps.banking.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# SPA fallback: any non-API, non-admin, non-static path serves the React app
# so client-side (react-router) routes work on hard refresh.
urlpatterns += [
    re_path(r"^(?!api/|admin/|static/|media/).*$", spa_index),
]
