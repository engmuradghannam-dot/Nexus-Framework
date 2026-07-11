from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ModuleRecordViewSet

router = DefaultRouter()
router.register(r"records", ModuleRecordViewSet, basename="module-record")

urlpatterns = [path("", include(router.urls))]
