"""Nexus Framework URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/core/', include('apps.core.urls')),
    path('api/pmo/', include('apps.pmo.urls')),
    path('api/industry/', include('apps.industry.urls')),
    path('api/ai/', include('apps.ai_module.urls')),
    path('api/regulatory/', include('apps.regulatory.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
