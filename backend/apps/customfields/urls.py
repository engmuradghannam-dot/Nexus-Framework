from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomControlViewSet,
    CustomFieldValueViewSet,
    CustomFieldViewSet,
)

router = DefaultRouter()
router.register(r"fields", CustomFieldViewSet, basename="custom-field")
router.register(r"values", CustomFieldValueViewSet, basename="custom-field-value")
router.register(r"controls", CustomControlViewSet, basename="custom-control")

urlpatterns = [path("", include(router.urls))]
