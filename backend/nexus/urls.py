"""Nexus Framework URL Configuration"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('rest_framework.urls')),
    path('api/pmo/', include('nexus.apps.pmo.urls')),
    path('api/industry/', include('nexus.apps.industry.urls')),
    path('api/ai/', include('nexus.apps.ai_module.urls')),
    path('api/regulatory/', include('nexus.apps.regulatory.urls')),
    path('api/core/', include('nexus.apps.core.urls')),
    path('api/hr/', include('nexus.apps.hr.urls')),
    path('api/ecommerce/', include('nexus.apps.ecommerce.urls')),
    path('api/workflow/', include('nexus.apps.workflow.urls')),
    path('api/permissions/', include('nexus.apps.permissions.urls')),
    path('api/accounting/', include('nexus.apps.accounting.urls')),
    path('api/docs/', include('nexus.yasg')),
]
