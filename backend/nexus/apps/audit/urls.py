from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChangeHeaderViewSet

router = DefaultRouter()
router.register(r'change-headers', ChangeHeaderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
