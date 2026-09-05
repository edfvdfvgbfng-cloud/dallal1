from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .api_views import PropertyViewSet, property_offers_api, property_offer_action_api, property_negotiations_api, negotiation_message_api, property_reservations_api, reservation_action_api, gps_nearby_properties_api, gps_area_search_api, gps_geocode_api, gps_reverse_geocode_api, gps_distance_api
from .chat_views import (
    ConversationViewSet, ChatMessageViewSet,
    MessageAttachmentViewSet, MessageReportViewSet,
    ChatSettingsViewSet, BlockedUserViewSet,
    user_list
)
from .views import create_admin_conversation
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
from .ai_smart_assistant_api import (
    smart_assistant_chat, smart_assistant_reset,
    smart_assistant_state, smart_assistant_confirm,
    smart_assistant_suggest_alternatives
)
from .ai_unified_search_service import ai_search_service


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
    path('create-admin-conversation/', create_admin_conversation, name='create-admin-conversation'),
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
    # Smart Assistant API endpoints
    path('ai/smart/chat/', smart_assistant_chat, name='smart-assistant-chat'),
    path('ai/smart/reset/', smart_assistant_reset, name='smart-assistant-reset'),
    path('ai/smart/state/', smart_assistant_state, name='smart-assistant-state'),
    path('ai/smart/confirm/', smart_assistant_confirm, name='smart-assistant-confirm'),
    path('ai/suggest-alternatives/', smart_assistant_suggest_alternatives, name='smart-assistant-suggest'),
    # Legacy endpoint - compatibility wrapper
    path('chatbot/', ai_chatbot_legacy, name='ai-chatbot-legacy'),
    # Property Offer & Negotiation API endpoints
    path('offers/', property_offers_api, name='property-offers'),
    path('offers/<int:property_id>/', property_offers_api, name='property-offers-detail'),
    path('offers/<int:offer_id>/action/', property_offer_action_api, name='property-offer-action'),
    path('negotiations/', property_negotiations_api, name='property-negotiations'),
    path('negotiations/<int:property_id>/', property_negotiations_api, name='property-negotiations-detail'),
    path('negotiations/<int:negotiation_id>/message/', negotiation_message_api, name='negotiation-message'),
    # Property Reservation API endpoints
    path('reservations/', property_reservations_api, name='property-reservations'),
    path('reservations/<int:property_id>/', property_reservations_api, name='property-reservations-detail'),
    path('reservations/<int:reservation_id>/action/', reservation_action_api, name='reservation-action'),
    # GPS and Location API endpoints
    path('gps/nearby/', gps_nearby_properties_api, name='gps-nearby-properties'),
    path('gps/area-search/', gps_area_search_api, name='gps-area-search'),
    path('gps/geocode/', gps_geocode_api, name='gps-geocode'),
    path('gps/reverse-geocode/', gps_reverse_geocode_api, name='gps-reverse-geocode'),
    path('gps/distance/', gps_distance_api, name='gps-distance'),
]
