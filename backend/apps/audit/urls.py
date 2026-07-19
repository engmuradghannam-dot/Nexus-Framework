from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .changedoc_api import ChangeDocumentViewSet

from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r"logs", AuditLogViewSet, basename="audit-log")
router.register(r"change-documents", ChangeDocumentViewSet, basename="change-document")

urlpatterns = [path("", include(router.urls))]
