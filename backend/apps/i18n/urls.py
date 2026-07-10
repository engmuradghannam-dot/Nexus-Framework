from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LanguageViewSet, TranslationImportJobViewSet, TranslationViewSet

router = DefaultRouter()
router.register(r"languages", LanguageViewSet, basename="language")
router.register(r"translations", TranslationViewSet, basename="translation")
router.register(r"import-jobs", TranslationImportJobViewSet, basename="translation-import-job")

urlpatterns = [
    path("", include(router.urls)),
]
