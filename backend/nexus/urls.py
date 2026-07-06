from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.observability.views import metrics_view, health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('nexus.api_urls')),
    path('api/v1/tenants/', include('apps.tenants.urls')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/plugins/', include('apps.core.plugin_system.urls')),
    path('metrics', metrics_view, name='prometheus-metrics'),
    path('health', health_check, name='health-check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
