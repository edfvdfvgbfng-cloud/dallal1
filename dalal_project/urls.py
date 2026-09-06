from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from properties.sitemaps import PropertySitemap, StaticViewSitemap

def health_check(request):
    """
    Production healthcheck endpoint for Railway.
    Safely verifies application and database connectivity without leaking credentials.
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        db_engine = connection.settings_dict.get('ENGINE', '').split('.')[-1]
        db_name = connection.settings_dict.get('NAME', '')
        safe_db_name = str(db_name).split('/')[-1] if isinstance(db_name, str) else 'database'

        return JsonResponse({
            'status': 'healthy',
            'service': 'dalal-backend',
            'database': {
                'status': 'connected',
                'engine': db_engine,
                'name': safe_db_name,
            },
            'time': str(timezone.now())
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'dalal-backend',
            'database': {
                'status': 'disconnected',
                'error': str(e) if settings.DEBUG else 'Database connection failure'
            },
            'time': str(timezone.now())
        }, status=503)

sitemaps = {
    'properties': PropertySitemap,
    'static': StaticViewSitemap,
}

# Swagger/OpenAPI Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="دلال API",
        default_version='v1',
        description="واجهة برمجة التطبيقات لمنصة دلال العقارية",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@dalal.iq"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def simple_home(request):
    """Simple home view for testing"""
    return JsonResponse({'status': 'ok', 'message': 'Home works', 'time': str(timezone.now())})

urlpatterns = [
    # Health check endpoint (first for Railway healthcheck)
    path('health/', health_check, name='health-check'),
    # Simple root view for testing
    path('', simple_home, name='simple-home'),
    # Include properties URLs as main path (includes dashboard/)
    path('app/', include('properties.urls')),
    # Admin panel
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/', include('properties.api_urls')),
    # Social Authentication
    path('social/', include('social_django.urls', namespace='social')),
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    # Sitemap and Robots
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots',
    ),
]

# Serve static and media files in DEBUG mode only
# In production, WhiteNoise handles static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
