# دلال (Dalal) Platform - Deployment Guide

This guide provides comprehensive instructions for deploying the Dalal real estate platform to Railway and GitHub Pages.

## Table of Contents

1. [Railway Deployment](#railway-deployment)
2. [GitHub Pages Deployment](#github-pages-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Troubleshooting](#troubleshooting)

---

## Railway Deployment

Railway is recommended for the main application deployment with PostgreSQL and Redis support.

### Prerequisites

- Railway account (free tier available)
- GitHub repository with the project code
- Railway CLI or GitHub integration

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the Python application

### Step 2: Configure Services

#### Database Service
1. Add a PostgreSQL service
2. Set environment variables:
   - `POSTGRES_USER`: your_username
   - `POSTGRES_PASSWORD`: your_password
   - `POSTGRES_DB`: dalal_db

#### Redis Service (for WebSocket support)
1. Add a Redis service
2. Note the Redis connection URL

#### Main Application Service
1. Configure the Python service with these environment variables:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secure-secret-key-here
DJANGO_SETTINGS_MODULE=dalal_project.settings
ALLOWED_HOSTS=your-railway-domain.railway.app

# Database
DATABASE_URL=postgresql://username:password@host:port/database_name

# Redis (for WebSocket)
REDIS_URL=redis://your-redis-url
USE_WEBSOCKETS=True

# AI Configuration (optional)
AI_ENABLED=False
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# File Storage (optional)
CDN_ENABLED=False
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Step 3: Deploy

1. Click "Deploy" on your main service
2. Railway will automatically:
   - Install dependencies from requirements.txt
   - Run migrations
   - Collect static files
   - Start the Gunicorn server

### Step 4: Verify Deployment

1. Check the deployment logs for any errors
2. Visit your Railway domain URL
3. Test the application functionality

### Step 5: Custom Domain (Optional)

1. Go to your service settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed

---

## GitHub Pages Deployment

GitHub Pages is used for serving static assets (CSS, JS, images) separately from the main application.

### Prerequisites

- GitHub repository
- GitHub Pages enabled

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to Settings → Pages
3. Source: Deploy from a branch
4. Branch: `main`
5. Folder: `/staticfiles`

### Step 2: Configure Workflow

The GitHub Actions workflow (`.github/workflows/github-pages.yml`) will automatically:
- Build static files
- Deploy them to GitHub Pages

### Step 3: Trigger Deployment

1. Push to the `main` branch
2. The workflow will automatically run
3. Static files will be available at `https://yourusername.github.io/your-repo/`

### Step 4: Update Settings

Update `dalal_project/settings.py` to use GitHub Pages CDN:

```python
# In production, use GitHub Pages for static files
if not DEBUG:
    STATIC_URL = 'https://yourusername.github.io/your-repo/static/'
```

---

## Docker Deployment

For local development or self-hosted deployment.

### Step 1: Build Docker Image

```bash
docker build -t dalal-platform:latest .
```

### Step 2: Run with Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
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

- Main application: http://localhost:8000
- Nginx proxy: http://localhost

### Step 4: Stop Services

```bash
docker-compose down
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Core Django
DEBUG=False
SECRET_KEY=your-secure-secret-key
DJANGO_SETTINGS_MODULE=dalal_project.settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (Required for Production)
DATABASE_URL=postgresql://user:password@host:port/database

# Redis (Required for WebSocket)
REDIS_URL=redis://your-redis-url
USE_WEBSOCKETS=True
```

### Optional Environment Variables

```bash
# AI Features
AI_ENABLED=False
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password

# File Storage
CDN_ENABLED=False
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Social Auth
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-client-secret
SOCIAL_AUTH_FACEBOOK_KEY=your-facebook-app-id
SOCIAL_AUTH_FACEBOOK_SECRET=your-facebook-app-secret

# Push Notifications
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIM_EMAIL=your-email
```

---

## Railway CI/CD Setup

### GitHub Actions Integration

1. Go to repository Settings → Secrets and variables → Actions
2. Add these secrets:
   - `RAILWAY_TOKEN`: Your Railway API token
   - `STAGING_URL`: Your Railway staging URL (optional)
   - `PRODUCTION_URL`: Your Railway production URL (optional)
   - `SLACK_WEBHOOK`: Slack webhook for notifications (optional)

3. The workflow `.github/workflows/railway-deploy.yml` will automatically deploy on push to main/develop branches.

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
**Problem:** Application can't connect to PostgreSQL

**Solution:**
- Verify DATABASE_URL is correct
- Check PostgreSQL service is running
- Ensure firewall allows connection

#### 2. Static Files Not Loading
**Problem:** CSS/JS files not served

**Solution:**
- Run `python manage.py collectstatic`
- Check STATIC_URL configuration
- Verify file permissions

#### 3. WebSocket Connection Failed
**Problem:** WebSocket connections not working

**Solution:**
- Ensure REDIS_URL is set
- Check USE_WEBSOCKETS=True
- Verify Redis service is running

#### 4. Migration Errors
**Problem:** Migrations fail to apply

**Solution:**
- Check database connection
- Run `python manage.py showmigrations`
- For Railway, check if DATABASE_URL is set before deployment

#### 5. Memory Issues
**Problem:** Application runs out of memory

**Solution:**
- Reduce Gunicorn workers: `--workers 2`
- Increase Railway service memory
- Enable database connection pooling

---

## Performance Optimization

### Railway-Specific

1. **Enable PostgreSQL Connection Pooling**
   ```python
   # In settings.py
   DATABASES['default']['CONN_MAX_AGE'] = 600
   ```

2. **Configure Redis Caching**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': REDIS_URL,
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

3. **Enable CDN for Static Files**
   - Configure Cloudinary or AWS S3
   - Update STATIC_URL to point to CDN

---

## Security Checklist

Before deploying to production:

- [ ] Set strong SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up PostgreSQL (not SQLite)
- [ ] Configure Redis for WebSocket
- [ ] Enable SSL/HTTPS
- [ ] Set up CORS properly
- [ ] Configure email backend
- [ ] Enable CSRF protection
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Remove sensitive data from code
- [ ] Update .env.example with real values

---

## Monitoring and Logging

### Railway Monitoring

1. Go to your service in Railway
2. View metrics in the "Metrics" tab
3. Check logs in the "Logs" tab
4. Set up alerts for CPU/memory usage

### Application Logging

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## Backup Strategy

### Railway Backup

Railway automatically backs up PostgreSQL databases. To restore:

1. Go to your PostgreSQL service
2. Click "Backups"
3. Select a backup to restore

### Manual Backup

```bash
# Backup database
docker-compose exec db pg_dump -U dalal_user dalal_db > backup.sql

# Restore database
docker-compose exec -T db psql -U dalal_user dalal_db < backup.sql
```

---

## Cost Estimation

### Railway Free Tier

- PostgreSQL: Free (1GB storage)
- Redis: Free (256MB memory)
- Application: $5/month (512MB RAM, 0.5 vCPU)

### Estimated Monthly Costs

- Development: $5-10/month
- Production: $20-50/month (depending on scale)

---

## Support

For issues or questions:

1. Check Railway documentation: https://docs.railway.app
2. Check GitHub Pages documentation: https://docs.github.com/pages
3. Review Django deployment guide: https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Last Updated:** 2026-09-05  
**Version:** 1.0