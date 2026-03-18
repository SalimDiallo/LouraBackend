# AI Module - URLs
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, ChatView, ChatStreamView, AIToolsView, AIConfigView

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', ChatView.as_view(), name='ai-chat'),
    path('chat/stream/', ChatStreamView.as_view(), name='ai-chat-stream'),
    path('tools/', AIToolsView.as_view(), name='ai-tools'),
    path('config/', AIConfigView.as_view(), name='ai-config'),
]
