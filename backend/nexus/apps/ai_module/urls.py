from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIModelViewSet, AIConversationViewSet, 
    AIMessageViewSet, AIPromptTemplateViewSet
)

router = DefaultRouter()
router.register(r'models', AIModelViewSet)
router.register(r'conversations', AIConversationViewSet)
router.register(r'messages', AIMessageViewSet)
router.register(r'prompt-templates', AIPromptTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
