from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomFieldValueViewSet, CustomFieldViewSet

router = DefaultRouter()
router.register(r"fields", CustomFieldViewSet, basename="custom-field")
router.register(r"values", CustomFieldValueViewSet, basename="custom-field-value")

urlpatterns = [path("", include(router.urls))]
