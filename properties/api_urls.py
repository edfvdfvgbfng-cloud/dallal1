from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .api_views import PropertyViewSet
from .chat_views import (
    ConversationViewSet, ChatMessageViewSet,
    MessageAttachmentViewSet, MessageReportViewSet,
    ChatSettingsViewSet, BlockedUserViewSet,
    user_list
)
from .ai_multimodal_api import (
    multimodal_chat, image_similarity_search,
    cv_job_matching, document_qa, pipeline_statistics
)
from .ai_market_orchestrator import market_intelligence_orchestrator
from .ai_market_api import (
    market_query, calculate_property_match,
    match_agents, market_analytics, market_summary
)
from .ai_gateway_api import (
    ai_chat, ai_multimodal, ai_market, ai_autonomous,
    conversation_state, clear_conversation, ai_chatbot_legacy
)


schema_view = get_schema_view(
    openapi.Info(
        title="دلال API",
        default_version='v1',
        description="API للعقارات العراقية - تصفح حسب المحافظة",
        terms_of_service="https://www.daluailiraq.com/terms/",
        contact=openapi.Contact(email="info@daluailiraq.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')

# Chat System Routes
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'attachments', MessageAttachmentViewSet, basename='messageattachment')
router.register(r'reports', MessageReportViewSet, basename='messagereport')
router.register(r'chat-settings', ChatSettingsViewSet, basename='chatsettings')
router.register(r'blocked-users', BlockedUserViewSet, basename='blockeduser')

urlpatterns = [
    path('users/', user_list, name='user-list'),
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Multimodal AI API endpoints
    path('ai/multimodal/chat/', multimodal_chat, name='multimodal-chat'),
    path('ai/multimodal/image-similarity/', image_similarity_search, name='image-similarity'),
    path('ai/multimodal/cv-matching/', cv_job_matching, name='cv-matching'),
    path('ai/multimodal/document-qa/', document_qa, name='document-qa'),
    path('ai/multimodal/statistics/', pipeline_statistics, name='pipeline-statistics'),
    # Market Intelligence API endpoints
    path('ai/market/query/', market_query, name='market-query'),
    path('ai/market/property-match/', calculate_property_match, name='property-match'),
    path('ai/market/agent-match/', match_agents, name='agent-match'),
    path('ai/market/analytics/', market_analytics, name='market-analytics'),
    path('ai/market/summary/', market_summary, name='market-summary'),
    # Unified AI Gateway endpoints
    path('ai/chat/', ai_chat, name='ai-chat'),
    path('ai/multimodal/', ai_multimodal, name='ai-multimodal'),
    path('ai/market/', ai_market, name='ai-market'),
    path('ai/autonomous/', ai_autonomous, name='ai-autonomous'),
    path('ai/conversation/state/', conversation_state, name='conversation-state'),
    path('ai/conversation/clear/', clear_conversation, name='clear-conversation'),
    # Legacy endpoint - compatibility wrapper
    path('chatbot/', ai_chatbot_legacy, name='ai-chatbot-legacy'),
]
