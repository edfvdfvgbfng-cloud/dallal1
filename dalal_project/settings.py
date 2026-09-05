"""
Django settings for dalal_project — production-ready configuration.
Supports SQLite (dev) and PostgreSQL (production) environment variables.
Cache bust: 2026-09-05-02-00
"""

import os
from pathlib import Path
import logging

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    try:
        from python_dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # No dotenv available, rely on system env vars

# Helper function to get config values (replaces decouple.config)
def config(key, default='', cast=str):
    """Get environment variable with optional type casting."""
    value = os.getenv(key, default)
    if cast == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    try:
        return cast(value)
    except (ValueError, TypeError):
        return default

# Helper function for CSV values (replaces decouple.Csv)
def Csv():
    """Return a function that parses comma-separated values."""
    return lambda v: [x.strip() for x in v.split(',') if x.strip()]

BASE_DIR = Path(__file__).resolve().parent.parent

# Configure logging
logger = logging.getLogger(__name__)


def _parse_csv_env(name, default=''):
    """Parse comma-separated env values; ignore placeholder entries."""
    raw = os.getenv(name, default)
    if not raw:
        return []
    invalid_items = {'.', '*'}
    return [
        item.strip()
        for item in raw.split(',')
        if item.strip() and item.strip() not in invalid_items
    ]


def _unique(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        # Generate a stronger development key
        import secrets
        SECRET_KEY = secrets.token_urlsafe(50)
        logger.warning("Using generated SECRET_KEY for development - change this in production!")
    else:
        raise ValueError('SECRET_KEY environment variable must be set in production')
elif len(SECRET_KEY) < 50 and not DEBUG:
    logger.warning("SECRET_KEY is less than 50 characters - consider using a longer key for better security")

# Custom domain
custom_domain = os.getenv('CUSTOM_DOMAIN', 'daluailiraq.com')

# Configure ALLOWED_HOSTS - Start with empty list for security
ALLOWED_HOSTS = []

# Add localhost only in DEBUG mode
if DEBUG:
    ALLOWED_HOSTS = _unique(ALLOWED_HOSTS + ['localhost', '127.0.0.1', '[::1]'])

# Add Railway domains
ALLOWED_HOSTS = _unique(ALLOWED_HOSTS + [
    '.railway.app',
    'healthcheck.railway.app',
    '.up.railway.app',
])

# Add custom domain if specified
if custom_domain:
    ALLOWED_HOSTS = _unique(ALLOWED_HOSTS + [custom_domain, f'www.{custom_domain}'])

# Add dynamic Railway public domain from environment
railway_public_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if railway_public_domain:
    ALLOWED_HOSTS = _unique(ALLOWED_HOSTS + [railway_public_domain])

# Add additional hosts from environment
ALLOWED_HOSTS = _unique(ALLOWED_HOSTS + _parse_csv_env('ALLOWED_HOSTS'))

# CSRF_TRUSTED_ORIGINS
if DEBUG:
    # In DEBUG mode, allow localhost for development
    # Add a wide range of local ports for browser preview
    local_ports = list(range(50000, 65000))
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost',
        'http://127.0.0.1',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ] + [f'http://127.0.0.1:{port}' for port in local_ports] + [f'http://localhost:{port}' for port in local_ports]
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    # In production, only allow Railway domains
    CSRF_TRUSTED_ORIGINS = _unique([
        'https://muqq.up.railway.app',
    ] + _parse_csv_env('CSRF_TRUSTED_ORIGINS'))

# Add dynamic domains to CSRF_TRUSTED_ORIGINS
if not DEBUG:
    if railway_public_domain:
        CSRF_TRUSTED_ORIGINS = _unique(CSRF_TRUSTED_ORIGINS + [f'https://{railway_public_domain}'])

    if custom_domain:
        CSRF_TRUSTED_ORIGINS = _unique(CSRF_TRUSTED_ORIGINS + [
            f'https://{custom_domain}',
            f'https://www.{custom_domain}',
        ])

# Silenced System Checks with Documentation
# security.W004: SECURE_SSL_REDIRECT and HSTS configuration are handled conditionally based on DEBUG
# 4_0.E001: SQLite is allowed in DEBUG mode only; production requires PostgreSQL
SILENCED_SYSTEM_CHECKS = ['security.W004', '4_0.E001']

# Security Enhancements
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True if not DEBUG else False
SECURE_HSTS_PRELOAD = True if not DEBUG else False

# Performance Optimizations
# CONN_MAX_AGE will be set in database configuration

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'corsheaders',
    'django_filters',
    'rest_framework',
    'drf_yasg',
    'dalal_project',
    'properties',
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'properties.middleware.ImageOptimizationMiddleware',
    'properties.middleware.CDNMiddleware',
]

ROOT_URLCONF = 'dalal_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'properties.context_processors.site_context',
                'properties.context_processors.oauth_context',
            ],
            'builtins': [
                'django.contrib.humanize.templatetags.humanize',
                'properties.templatetags.custom_filters',
                'properties.templatetags.price_filters',
            ],
        },
    },
]

WSGI_APPLICATION = 'dalal_project.wsgi.application'

# Optional WebSocket support
USE_WEBSOCKETS = os.getenv('USE_WEBSOCKETS', 'False').lower() == 'true'
if USE_WEBSOCKETS:
    try:
        import channels  # noqa: F401
        if 'channels' not in INSTALLED_APPS:
            INSTALLED_APPS.insert(0, 'channels')
        ASGI_APPLICATION = 'dalal_project.asgi.application'
        
        # WebSocket Settings - Production requires Redis
        if not DEBUG:
            if not os.getenv('REDIS_URL'):
                logger.warning("Redis URL not set for WebSocket in production - falling back to InMemoryChannelLayer (not recommended for multi-worker)")
                CHANNEL_LAYERS = {
                    'default': {
                        'BACKEND': 'channels.layers.InMemoryChannelLayer',
                    },
                }
            else:
                CHANNEL_LAYERS = {
                    'default': {
                        'BACKEND': 'channels_redis.core.RedisChannelLayer',
                        'CONFIG': {
                            'hosts': [os.getenv('REDIS_URL')],
                        },
                    },
                }
        else:
            # Development - use InMemoryChannelLayer
            CHANNEL_LAYERS = {
                'default': {
                    'BACKEND': 'channels.layers.InMemoryChannelLayer',
                },
            }
    except ImportError:
        USE_WEBSOCKETS = False
else:
    # Add channels to INSTALLED_APPS for potential use
    try:
        import channels  # noqa: F401
        if 'channels' not in INSTALLED_APPS:
            INSTALLED_APPS.insert(0, 'channels')
    except ImportError:
        pass

# --- Database Configuration (ZERO DATA LOSS & POSTGRESQL ENFORCEMENT) ---
import dj_database_url

# Determine if production environment or strict PostgreSQL mode
IS_PRODUCTION_DEPLOYMENT = (
    not DEBUG or
    bool(os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID') or os.getenv('RAILWAY_SERVICE_ID')) or
    os.getenv('ALLOW_SQLITE_FALLBACK', 'True').lower() in ('false', '0', 'no') or
    os.getenv('ENVIRONMENT', '').lower() == 'production'
)

database_url = os.getenv('DATABASE_URL')

if not database_url:
    db_name = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB')
    db_user = os.getenv('DB_USER') or os.getenv('POSTGRES_USER')
    db_password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD')
    db_host = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST')
    db_port = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT', '5432')

    if db_name and db_user and db_password and db_host:
        database_url = f'postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# Validate database URL - reject placeholder or corrupt values
if database_url:
    invalid_patterns = ['@host:', 'user:password@', 'example.com', 'dummy']
    if any(pattern in database_url for pattern in invalid_patterns):
        database_url = None

if database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # CRITICAL: In production or strict mode, engine MUST be PostgreSQL
    if IS_PRODUCTION_DEPLOYMENT and 'postgres' not in DATABASES['default']['ENGINE'].lower():
        raise RuntimeError(
            f"CRITICAL ZERO-DATA-LOSS ERROR: Invalid database engine '{DATABASES['default']['ENGINE']}' in Production. "
            "Railway deployment must use PostgreSQL. SQLite fallback is strictly blocked to prevent data loss."
        )
elif not IS_PRODUCTION_DEPLOYMENT:
    # Development only: allow SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    raise RuntimeError(
        "CRITICAL ZERO-DATA-LOSS ERROR: DATABASE_URL is missing in Production environment! "
        "Railway deployment MUST be connected to an existing PostgreSQL service. "
        "Application will FAIL FAST and NOT create a new/empty SQLite database, guaranteeing zero data loss."
    )

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Baghdad'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ROOT = None
WHITENOISE_IGNORE_CONTENT_TYPE = ['webp', 'woff2']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# --- Security ---
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie Security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = 'Lax'

# Production Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # For Railway with HTTPS, use None for SameSite to allow cross-site cookies
    SESSION_COOKIE_SAMESITE = None
    CSRF_COOKIE_SAMESITE = None
else:
    # Development security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Additional security headers
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    # For Railway HTTPS compatibility in debug mode
    if railway_public_domain:
        SESSION_COOKIE_SAMESITE = None
        CSRF_COOKIE_SAMESITE = None

CSRF_USE_SESSIONS = False
CSRF_COOKIE_AGE = 3600 * 24 * 7  # 7 days
SESSION_COOKIE_AGE = 3600 * 24 * 7

# Use database-backed sessions to share sessions across multiple workers
# LocMemCache was causing sessions to be lost with workers=2
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# --- File Upload Security ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024   # 15MB (for property images/videos)
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024   # 15MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Rate limiting for API endpoints
RATELIMIT_ENABLE = os.getenv('RATELIMIT_ENABLE', 'True').lower() == 'true'
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'properties.api_views.ratelimit_view'

# Email Configuration for notifications
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@daluailiraq.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'admin@daluailiraq.com')

# Logging for API requests
API_REQUEST_LOGGING = os.getenv('API_REQUEST_LOGGING', 'True').lower() == 'true'

# Error Reporting
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment='production' if not DEBUG else 'development',
        )
        logger.info("Sentry error reporting enabled")
    except ImportError:
        logger.warning("Sentry SDK not installed - error reporting disabled")

# Monitoring and Health Checks
HEALTH_CHECK_ENABLED = os.getenv('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
HEALTH_CHECK_SECRET = os.getenv('HEALTH_CHECK_SECRET', '')

# Performance Monitoring
PERFORMANCE_MONITORING = os.getenv('PERFORMANCE_MONITORING', 'False').lower() == 'true'

# Database Connection Pooling
DATABASE_CONNECTION_POOL_SIZE = int(os.getenv('DATABASE_CONNECTION_POOL_SIZE', '10'))

# Database Query Optimization
DATABASE_QUERY_TIMEOUT = int(os.getenv('DATABASE_QUERY_TIMEOUT', '30'))
DATABASE_MAX_CONNECTIONS = int(os.getenv('DATABASE_MAX_CONNECTIONS', '20'))

# Caching Strategy
CACHE_TIMEOUT_DEFAULT = int(os.getenv('CACHE_TIMEOUT_DEFAULT', '300'))  # 5 minutes
CACHE_TIMEOUT_STATIC = int(os.getenv('CACHE_TIMEOUT_STATIC', '3600'))  # 1 hour
CACHE_TIMEOUT_QUERY = int(os.getenv('CACHE_TIMEOUT_QUERY', '180'))  # 3 minutes

# Session Security Enhancements
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_DOMAIN = None  # Will be set dynamically based on domain

# Content Security Policy (CSP) Headers
# This will be implemented via middleware for more flexibility
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
CSP_IMG_SRC = ["'self'", "data:", "https:"]
CSP_FONT_SRC = ["'self'", "data:"]
CSP_CONNECT_SRC = ["'self'"]
CSP_FRAME_SRC = ["'none'"]
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_BASE_URI = ["'self'"]
CSP_FORM_ACTION = ["'self'"]

# Performance Settings
USE_ETAGS = True
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Thumbnail generation settings
THUMBNAIL_QUALITY = 85
THUMBNAIL_SIZE = (800, 600)
THUMBNAIL_FORMAT = 'JPEG'

# Image Optimization Settings
IMAGE_OPTIMIZATION_ENABLED = os.getenv('IMAGE_OPTIMIZATION_ENABLED', 'True').lower() == 'true'
IMAGE_CONVERT_TO_WEBP = os.getenv('IMAGE_CONVERT_TO_WEBP', 'True').lower() == 'true'
IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '85'))
IMAGE_WEBP_QUALITY = int(os.getenv('IMAGE_WEBP_QUALITY', '80'))

# File Upload Security Settings
UPLOAD_MAX_FILE_SIZE = int(os.getenv('UPLOAD_MAX_FILE_SIZE', '10485760'))  # 10MB default
UPLOAD_ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
UPLOAD_ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'webm', 'mov', 'avi']
UPLOAD_ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
UPLOAD_MAX_IMAGE_DIMENSIONS = (4096, 4096)  # 4K max resolution
UPLOAD_SCAN_MALWARE = os.getenv('UPLOAD_SCAN_MALWARE', 'False').lower() == 'true'
UPLOAD_USE_UUID_FILENAMES = os.getenv('UPLOAD_USE_UUID_FILENAMES', 'True').lower() == 'true'

# Sensitive Document Storage (separate from public media)
UPLOAD_SENSITIVE_PATH = 'private_documents/'  # For identity docs, contracts, etc.
UPLOAD_PUBLIC_PATH = 'media/'  # For regular property images

# CDN Settings
CDN_ENABLED = os.getenv('CDN_ENABLED', 'False').lower() == 'true'
CDN_PROVIDER = os.getenv('CDN_PROVIDER', '')  # 'cloudinary', 'aws_s3', 'imgix'
CDN_BASE_URL = os.getenv('CDN_BASE_URL', '')

# Cloudinary Settings
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', '')

# Imgix Settings
IMGIX_DOMAIN = os.getenv('IMGIX_DOMAIN', '')
IMGIX_SIGN_KEY = os.getenv('IMGIX_SIGN_KEY', '')

# GPS and Geocoding Settings
GEOCODING_ENABLED = os.getenv('GEOCODING_ENABLED', 'False').lower() == 'true'
GEOCODING_PROVIDER = os.getenv('GEOCODING_PROVIDER', '')  # 'google', 'mapbox', 'here'
GEOCODING_API_KEY = os.getenv('GEOCODING_API_KEY', '')

# AI Configuration
AI_ENABLED = os.getenv('AI_ENABLED', 'False').lower() == 'true'
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai', 'anthropic', 'huggingface'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '2000'))
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))

# AI Safety Configuration
AI_RATE_LIMIT_ENABLED = os.getenv('AI_RATE_LIMIT_ENABLED', 'True').lower() == 'true'
AI_RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv('AI_RATE_LIMIT_REQUESTS_PER_MINUTE', '20'))
AI_CONTENT_MODERATION_ENABLED = os.getenv('AI_CONTENT_MODERATION_ENABLED', 'True').lower() == 'true'
AI_LOGGING_ENABLED = os.getenv('AI_LOGGING_ENABLED', 'False').lower() == 'true'  # Log AI interactions in production
AI_SAFE_MODE = os.getenv('AI_SAFE_MODE', 'True').lower() == 'true'  # Restrict AI from sensitive operations

# GPS Search Settings
GPS_SEARCH_RADIUS_KM = int(os.getenv('GPS_SEARCH_RADIUS_KM', '10'))
GPS_CLUSTER_RADIUS_KM = float(os.getenv('GPS_CLUSTER_RADIUS_KM', '0.5'))
GPS_MIN_CLUSTER_SIZE = int(os.getenv('GPS_MIN_CLUSTER_SIZE', '3'))

# Media file validation
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov']
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

# API throttling settings
API_THROTTLE_RATE = '1000/hour'
API_THROTTLE_ANON = '100/hour'

# Background task settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', '')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', '')
CELERY_TASK_ALWAYS_EAGER = DEBUG  # Run tasks synchronously in debug mode

# Geographic and Map Settings
DEFAULT_MAP_CENTER_LAT = 33.3152  # Baghdad latitude
DEFAULT_MAP_CENTER_LNG = 44.3661  # Baghdad longitude
DEFAULT_MAP_ZOOM = 12
MAP_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
MAP_ATTRIBUTION = '© OpenStreetMap contributors'

# Search and Filtering
SEARCH_MIN_CHARS = 2
SEARCH_MAX_RESULTS = 100
FILTER_MAX_OPTIONS = 50

# Notification settings
NOTIFICATION_EXPIRY_DAYS = 30
NOTIFICATION_MAX_PER_USER = 1000

# Broker and User Settings
MAX_PROPERTIES_PER_BROKER = int(os.getenv('MAX_PROPERTIES_PER_BROKER', '100'))
MAX_IMAGES_PER_PROPERTY = int(os.getenv('MAX_IMAGES_PER_PROPERTY', '20'))
MAX_VIDEOS_PER_PROPERTY = int(os.getenv('MAX_VIDEOS_PER_PROPERTY', '5'))

# Maintenance mode
MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'
MAINTENANCE_MESSAGE = os.getenv('MAINTENANCE_MESSAGE', 'الموقع قيد الصيانة - سنعود قريباً')

# Feature flags
FEATURE_ENABLED_PROPERTY_OFFERS = os.getenv('FEATURE_ENABLED_PROPERTY_OFFERS', 'True').lower() == 'true'
FEATURE_ENABLED_NEGOTIATIONS = os.getenv('FEATURE_ENABLED_NEGOTIATIONS', 'True').lower() == 'true'
FEATURE_ENABLED_RESERVATIONS = os.getenv('FEATURE_ENABLED_RESERVATIONS', 'True').lower() == 'true'
FEATURE_ENABLED_INTERACTIVE_MAP = os.getenv('FEATURE_ENABLED_INTERACTIVE_MAP', 'True').lower() == 'true'
FEATURE_ENABLED_AI_SEARCH = os.getenv('FEATURE_ENABLED_AI_SEARCH', 'False').lower() == 'true'
FEATURE_ENABLED_VIRTUAL_TOURS = os.getenv('FEATURE_ENABLED_VIRTUAL_TOURS', 'True').lower() == 'true'

# Backup and Recovery
BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'True').lower() == 'true'
BACKUP_SCHEDULE = os.getenv('BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

# Analytics and Monitoring
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'False').lower() == 'true'
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
FACEBOOK_PIXEL_ID = os.getenv('FACEBOOK_PIXEL_ID', '')

# SEO and Social Media
SEO_DEFAULT_TITLE = os.getenv('SEO_DEFAULT_TITLE', 'دلال - منصة العقارات العراقية')
SEO_DEFAULT_DESCRIPTION = os.getenv('SEO_DEFAULT_DESCRIPTION', 'أفضل منصة للبحث عن العقارات في العراق')
SEO_DEFAULT_KEYWORDS = os.getenv('SEO_DEFAULT_KEYWORDS', 'عقارات, عقارات العراق, بيع, شراء, تأجير, دلال')
SOCIAL_SHARE_IMAGE = os.getenv('SOCIAL_SHARE_IMAGE', '/static/images/og-default.jpg')

# Development helpers
if DEBUG:
    # Show detailed error pages
    DEBUG_TOOLBAR_ENABLED = os.getenv('DEBUG_TOOLBAR_ENABLED', 'False').lower() == 'true'
    if DEBUG_TOOLBAR_ENABLED:
        try:
            import debug_toolbar  # noqa: F401
            if 'debug_toolbar' not in INSTALLED_APPS:
                INSTALLED_APPS.append('debug_toolbar')
            if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
                MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
            INTERNAL_IPS = ['127.0.0.1', 'localhost']
        except ImportError:
            pass
    
    # Enable Django extensions for development
    try:
        import django_extensions  # noqa: F401
        if 'django_extensions' not in INSTALLED_APPS:
            INSTALLED_APPS.append('django_extensions')
    except ImportError:
        pass

# --- Cache ---
# Enhanced cache configuration for performance
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dalal-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    },
    'static_data': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dalal-static-cache',
        'TIMEOUT': 3600,  # 1 hour for static data
        'OPTIONS': {
            'MAX_ENTRIES': 500,
            'CULL_FREQUENCY': 2,
        }
    },
    'query_results': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dalal-query-cache',
        'TIMEOUT': 300,  # 5 minutes for query results
        'OPTIONS': {
            'MAX_ENTRIES': 2000,
            'CULL_FREQUENCY': 5,
        }
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dalal-sessions',
        'TIMEOUT': 3600,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    },
}

if os.getenv('REDIS_URL') and not DEBUG:
    try:
        import django_redis  # noqa: F401
        CACHES['default'] = {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'dalal',
            'TIMEOUT': CACHE_TIMEOUT_DEFAULT,
        }
    except ImportError:
        pass

# Apply cache timeout environment variables
CACHES['default']['TIMEOUT'] = CACHE_TIMEOUT_DEFAULT
CACHES['static_data']['TIMEOUT'] = CACHE_TIMEOUT_STATIC
CACHES['query_results']['TIMEOUT'] = CACHE_TIMEOUT_QUERY

# Enable cache middleware for performance
if not DEBUG:
    CACHE_MIDDLEWARE_ALIAS = 'default'
    CACHE_MIDDLEWARE_SECONDS = CACHE_TIMEOUT_DEFAULT
    CACHE_MIDDLEWARE_KEY_PREFIX = 'dalal'
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = False

# --- Logging ---
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'dalal.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'security.log',
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'api_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'api.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'WARNING', 'propagate': False},
        'django.security': {'handlers': ['console', 'file', 'security_file'], 'level': 'WARNING', 'propagate': False},
        'properties': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'properties.api_views': {'handlers': ['console', 'file', 'api_file'], 'level': 'INFO', 'propagate': False},
    },
}

# --- Messages ---
from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: 'info',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error',
}

SITE_NAME = os.getenv('SITE_NAME', 'دلال')

# --- Social Authentication ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Add OAuth backends only if keys are available
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '').strip()
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '').strip()
SOCIAL_AUTH_FACEBOOK_KEY = os.getenv('SOCIAL_AUTH_FACEBOOK_KEY', '').strip()
SOCIAL_AUTH_FACEBOOK_SECRET = os.getenv('SOCIAL_AUTH_FACEBOOK_SECRET', '').strip()

# تحديد ما إذا كانت مصادقة Google متاحة
GOOGLE_AUTH_AVAILABLE = bool(SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET)
FACEBOOK_AUTH_AVAILABLE = bool(SOCIAL_AUTH_FACEBOOK_KEY and SOCIAL_AUTH_FACEBOOK_SECRET)

# Add backends conditionally
if GOOGLE_AUTH_AVAILABLE:
    AUTHENTICATION_BACKENDS.append('social_core.backends.google.GoogleOAuth2')

if FACEBOOK_AUTH_AVAILABLE:
    AUTHENTICATION_BACKENDS.append('social_core.backends.facebook.FacebookOAuth2')

RAILWAY_PUBLIC_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
# Also check for alternative Railway domains from ALLOWED_HOSTS
if RAILWAY_PUBLIC_DOMAIN:
    BASE_URL = f'https://{RAILWAY_PUBLIC_DOMAIN}'
elif custom_domain:
    BASE_URL = f'https://{custom_domain}'
else:
    BASE_URL = 'http://127.0.0.1:8000'

# Override BASE_URL if we detect muqq.up.railway.app from request headers
# This is handled dynamically in middleware, but we need a fallback here

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name', 'picture']
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = f'{BASE_URL}/social/complete/google-oauth2/'

SOCIAL_AUTH_FACEBOOK_OAUTH2_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_OAUTH2_EXTRA_DATA = ['first_name', 'last_name', 'picture']
SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI = f'{BASE_URL}/social/complete/facebook/'

SOCIAL_AUTH_CSRF_IGNORE = True
SOCIAL_AUTH_ALLOW_REDIRECT_URI_CHANGE = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = not DEBUG

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'properties.social_auth.save_profile_picture',
    'properties.social_auth.save_social_data',
    'properties.social_auth.social_auth_error',
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/'
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/dashboard/'
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = '/settings/social/'

SOCIAL_AUTH_USER_MODEL = 'auth.User'
SOCIAL_AUTH_FORCE_RANDOM_USERNAME = False
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_SLUGIFY_USERNAMES = 'lower'
SOCIAL_AUTH_SANITIZE_USERNAMES = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# CORS Settings - Explicit list for security
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Add preview URLs for development
if DEBUG:
    # Allow all localhost ports for development
    import re
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:*",
        "http://127.0.0.1:*",
    ]
    CORS_ALLOW_HEADERS = ['*']
    CORS_ALLOW_CREDENTIALS = True

# Add Railway domains in production
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://muqq.up.railway.app",
    ]
    if railway_public_domain:
        CORS_ALLOWED_ORIGINS.append(f"https://{railway_public_domain}")
    if custom_domain:
        CORS_ALLOWED_ORIGINS.extend([
            f"https://{custom_domain}",
            f"https://www.{custom_domain}",
        ])

# Web Push Notifications (VAPID)
# IMPORTANT: Generate proper VAPID keys for production and set via environment variables
# Do not use default keys in production - they are for development only
if DEBUG:
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'VjUzWIXpq7KSwl1uZ9jO69d1XFSu2TyufTTnHdXGqfc')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 'yynegj8EQiW5I4_vUco176PriO6H6wAAf8aWfHvlY4E')
    VAPID_CLAIM_EMAIL = os.getenv('VAPID_CLAIM_EMAIL', 'admin@dalal.com')
else:
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
    VAPID_CLAIM_EMAIL = os.getenv('VAPID_CLAIM_EMAIL', 'admin@daluailiraq.com')
    
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not set - push notifications will not work in production")

# CSRF Settings for AJAX
# CSRF_TRUSTED_ORIGINS is already configured above based on DEBUG mode

if DEBUG:
    # Allow all origins for development (including preview ports)
    for port in range(50000, 70000):
        CSRF_TRUSTED_ORIGINS.append(f"http://127.0.0.1:{port}")
        CSRF_TRUSTED_ORIGINS.append(f"http://localhost:{port}")
    # CSRF cookie security is already set above based on DEBUG mode