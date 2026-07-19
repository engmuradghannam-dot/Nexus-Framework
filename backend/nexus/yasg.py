from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Nexus Framework API",
        default_version='v1',
        description="""
        Nexus Framework - Enterprise Resource Planning API

        ## Modules
        * **Core** - Companies, Branches, Warehouses, HR
        * **PMO** - Projects, Tasks, Milestones
        * **Industry** - Products, Inventory, Suppliers, Purchase Orders
        * **AI** - Conversations, Models, Prompt Templates
        * **Regulatory** - Regulations, Compliance Checks
        """,
        terms_of_service="https://github.com/engmuradghannam-dot/Nexus-Framework",
        contact=openapi.Contact(email="support@nexus-framework.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
