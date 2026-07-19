from rest_framework.routers import DefaultRouter

from .views import ApprovalRequestViewSet, ReleaseStrategyViewSet

router = DefaultRouter()
router.register(r"strategies", ReleaseStrategyViewSet, basename="release-strategy")
router.register(r"requests", ApprovalRequestViewSet, basename="approval-request")

urlpatterns = router.urls
