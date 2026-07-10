"""Nexus Framework URL Configuration"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.admin_site import admin_site

urlpatterns = [
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
