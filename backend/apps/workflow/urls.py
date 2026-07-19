from rest_framework.routers import DefaultRouter

from .views import WorkflowInstanceViewSet, WorkflowViewSet

router = DefaultRouter()
router.register(r"workflows", WorkflowViewSet, basename="workflow")
router.register(r"instances", WorkflowInstanceViewSet, basename="workflow-instance")

urlpatterns = router.urls
