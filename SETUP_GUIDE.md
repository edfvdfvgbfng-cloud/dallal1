# دلال (Dalal) Platform - Environment Setup Guide

This guide provides step-by-step instructions for setting up the Dalal platform environment for deployment.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dalal-platform.git
cd dalal-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

---

## Detailed Environment Configuration

### Required Variables

These variables must be set for production deployment:

```bash
# Core Django Settings
DEBUG=False
SECRET_KEY=generate-a-secure-50-character-key
DJANGO_SETTINGS_MODULE=dalal_project.settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (Required)
DATABASE_URL=postgresql://username:password@host:5432/database_name

# Redis (Required for WebSocket)
REDIS_URL=redis://username:password@host:6379/0
USE_WEBSOCKETS=True
```

### Generating Secure Keys

#### SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(50))
```

#### VAPID Keys (for Push Notifications)

```bash
# Generate VAPID keys
pip install pywebpush
python -c "from pywebpush import WebPusher; print(WebPusher.generate_vapid_keys())"
```

---

## Railway-Specific Setup

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Install Railway CLI: `npm install -g @railway/cli`

### Step 2: Initialize Project

```bash
railway login
railway init
```

### Step 3: Add Services

#### PostgreSQL Database

```bash
railway add postgresql
```

#### Redis (for WebSocket)

```bash
railway add redis
```

#### Main Application

```bash
railway up
```

### Step 4: Configure Environment Variables

In Railway dashboard, set these variables for your main service:

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
DJANGO_SETTINGS_MODULE=dalal_project.settings
ALLOWED_HOSTS=your-app.railway.app

# Database (Railway provides this automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (Railway provides this automatically)
REDIS_URL=${{Redis.REDIS_URL}}
USE_WEBSOCKETS=True

# Optional Features
AI_ENABLED=False
CDN_ENABLED=False
```

### Step 5: Deploy

```bash
railway up
```

---

## GitHub Pages Setup

### Step 1: Enable GitHub Pages

1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`
4. Folder: `/staticfiles`

### Step 2: Configure CDN (Optional)

Update `dalal_project/settings.py`:

```python
if not DEBUG:
    # Use GitHub Pages for static files
    STATIC_URL = 'https://yourusername.github.io/dalal-platform/static/'
    MEDIA_URL = 'https://yourusername.github.io/dalal-platform/media/'
```

### Step 3: Update GitHub Actions

The workflow in `.github/workflows/github-pages.yml` will automatically deploy static files on push to main branch.

---

## Docker Setup

### Step 1: Build Image

```bash
docker build -t dalal-platform:latest .
```

### Step 2: Run with Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit .env
nano .env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### Step 3: Access Application

- Main app: http://localhost:8000
- Nginx proxy: http://localhost

---

## Production Environment Variables

### Complete .env Example

```bash
# ============================================================================
# CORE DJANGO SETTINGS
# ============================================================================
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-minimum-50-characters
DJANGO_SETTINGS_MODULE=dalal_project.settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# Railway provides DATABASE_URL automatically
# DATABASE_URL=postgresql://user:password@host:5432/database_name

# ============================================================================
# REDIS CONFIGURATION (for WebSocket & Caching)
# ============================================================================
# Railway provides REDIS_URL automatically
# REDIS_URL=redis://user:password@host:6379/0
USE_WEBSOCKETS=True

# ============================================================================
# AI CONFIGURATION
# ============================================================================
AI_ENABLED=False
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key
AI_MODEL=gpt-3.5-turbo
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_RATE_LIMIT_ENABLED=True
AI_RATE_LIMIT_REQUESTS_PER_MINUTE=20
AI_CONTENT_MODERATION_ENABLED=True
AI_LOGGING_ENABLED=False
AI_SAFE_MODE=True

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=admin@yourdomain.com

# ============================================================================
# FILE STORAGE & CDN
# ============================================================================
CDN_ENABLED=False
CDN_PROVIDER=cloudinary
CDN_BASE_URL=
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# AWS S3 (Alternative to Cloudinary)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION=us-east-1
AWS_S3_CUSTOM_DOMAIN=

# ============================================================================
# SOCIAL AUTHENTICATION
# ============================================================================
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-client-secret
SOCIAL_AUTH_FACEBOOK_KEY=your-facebook-app-id
SOCIAL_AUTH_FACEBOOK_SECRET=your-facebook-app-secret

# ============================================================================
# PUSH NOTIFICATIONS
# ============================================================================
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIM_EMAIL=admin@yourdomain.com

# ============================================================================
# GPS & GEOCODING
# ============================================================================
GEOCODING_ENABLED=False
GEOCODING_PROVIDER=google
GEOCODING_API_KEY=your-google-maps-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# ============================================================================
# FILE UPLOAD SECURITY
# ============================================================================
UPLOAD_MAX_FILE_SIZE=10485760
UPLOAD_MAX_IMAGE_DIMENSIONS=4096
UPLOAD_SCAN_MALWARE=False
UPLOAD_USE_UUID_FILENAMES=True

# ============================================================================
# FEATURE FLAGS
# ============================================================================
FEATURE_ENABLED_PROPERTY_OFFERS=True
FEATURE_ENABLED_NEGOTIATIONS=True
FEATURE_ENABLED_RESERVATIONS=True
FEATURE_ENABLED_INTERACTIVE_MAP=True
FEATURE_ENABLED_AI_SEARCH=False
FEATURE_ENABLED_VIRTUAL_TOURS=True

# ============================================================================
# MAINTENANCE MODE
# ============================================================================
MAINTENANCE_MODE=False
MAINTENANCE_MESSAGE=الموقع قيد الصيانة - سنعود قريباً

# ============================================================================
# MONITORING & LOGGING
# ============================================================================
API_REQUEST_LOGGING=True
SENTRY_DSN=your-sentry-dsn  # Optional
```

---

## Security Best Practices

### 1. Never Commit Secrets

- Never commit `.env` file
- Never commit API keys or passwords
- Use environment variables for all sensitive data

### 2. Use Strong Secrets

```bash
# Generate strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate strong database password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Enable HTTPS

```bash
# In production
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 4. Configure CORS

```python
# In settings.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## Testing Your Setup

### Test Database Connection

```bash
python manage.py dbshell
```

### Test Redis Connection

```python
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'
```

### Test Email Configuration

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test Subject', 'Test Body', 'from@example.com', ['to@example.com'])
```

### Test Static Files

```bash
python manage.py collectstatic --dry-run
```

---

## Production Checklist

Before deploying to production, ensure:

- [ ] DEBUG=False
- [ ] Strong SECRET_KEY set
- [ ] ALLOWED_HOSTS configured
- [ ] PostgreSQL database (not SQLite)
- [ ] Redis configured for WebSocket
- [ ] SSL/HTTPS enabled
- [ ] CORS properly configured
- [ ] Email backend configured
- [ ] Static files CDN configured
- [ ] CDN or object storage for media files
- [ ] Monitoring/logging configured
- [ ] Backup strategy in place
- [ ] Environment variables not committed
- [ ] Database migrations tested
- [ ] Superuser account created
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] AI features properly secured

---

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
python manage.py dbshell

# Check DATABASE_URL format
# Should be: postgresql://user:password@host:port/database
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h your-redis-host ping

# Check REDIS_URL format
# Should be: redis://:password@host:port/db
```

### Static Files Not Loading

```bash
# Check static files
python manage.py collectstatic --dry-run

# Verify STATIC_URL
python manage.py shell
>>> from django.conf import settings
>>> settings.STATIC_URL
```

### WebSocket Not Working

```bash
# Check Redis and WebSocket settings
# Ensure USE_WEBSOCKETS=True
# Ensure REDIS_URL is set
```

---

## Getting Help

For issues:

1. Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
2. Review [Production Audit Report](PRODUCTION_AUDIT_REPORT.md)
3. Check Railway documentation: https://docs.railway.app
4. Check Django deployment docs: https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Last Updated:** 2026-09-05  
**Version:** 1.0