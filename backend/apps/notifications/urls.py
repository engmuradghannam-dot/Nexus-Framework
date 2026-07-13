from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationLogViewSet, NotificationTemplateViewSet

router = DefaultRouter()
router.register(r"templates", NotificationTemplateViewSet, basename="notif-template")
router.register(r"log", NotificationLogViewSet, basename="notif-log")

urlpatterns = [path("", include(router.urls))]
