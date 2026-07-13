from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomFieldViewSet

router = DefaultRouter()
router.register(r"fields", CustomFieldViewSet, basename="custom-field")

urlpatterns = [path("", include(router.urls))]
