from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MilestoneViewSet,
    PortfolioViewSet,
    ProjectViewSet,
    TaskViewSet,
)

router = DefaultRouter()
router.register(r"portfolios", PortfolioViewSet, basename="portfolio")
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"milestones", MilestoneViewSet, basename="milestone")

urlpatterns = [
    path("", include(router.urls)),
]
