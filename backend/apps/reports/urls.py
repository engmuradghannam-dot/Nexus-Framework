from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReportDefinitionViewSet

router = DefaultRouter()
router.register(r"definitions", ReportDefinitionViewSet, basename="report-definition")

urlpatterns = [path("", include(router.urls))]
