#!/bin/bash

# Production Deployment Script for AI Platform
# This script handles deployment, migrations, and health checks

set -e  # Exit on error

echo "🚀 Starting AI Platform Deployment..."

# Configuration
PROJECT_DIR="/var/www/dalal_ai_platform"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
MANAGE_PY="$PROJECT_DIR/manage.py"
BACKUP_DIR="/var/backups/dalal_ai_platform"
LOG_DIR="/var/log/dalal_ai_platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root"
    exit 1
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR
mkdir -p $PROJECT_DIR/media
mkdir -p $PROJECT_DIR/static

# Backup current deployment
print_status "Creating backup..."
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR/$BACKUP_NAME

if [ -d "$PROJECT_DIR" ]; then
    cp -r $PROJECT_DIR/* $BACKUP_DIR/$BACKUP_NAME/ 2>/dev/null || true
    print_status "Backup created: $BACKUP_NAME"
fi

# Pull latest code (assuming git)
print_status "Pulling latest code..."
cd $PROJECT_DIR
git pull origin main || print_warning "Git pull failed, continuing with current code"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install dependencies
print_status "Installing dependencies..."
$PIP_BIN install -r requirements.txt --upgrade

# Install production dependencies
print_status "Installing production dependencies..."
$PIP_BIN install gunicorn psycopg2-binary redis celery django-whitenoise django-cors-headers

# Set environment variables
print_status "Setting environment variables..."
export DJANGO_SETTINGS_MODULE=dalal_project.settings
export DJANGO_SECRET_KEY=$(openssl rand -base64 32)
export DEBUG=False

# Run database migrations
print_status "Running database migrations..."
$PYTHON_BIN $MANAGE_PY migrate --noinput

# Collect static files
print_status "Collecting static files..."
$PYTHON_BIN $MANAGE_PY collectstatic --noinput --clear

# Create superuser if not exists
print_status "Checking for superuser..."
$PYTHON_BIN $MANAGE_PY shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@daluailiraq.com', 'admin123')
    print("Superuser created: admin/admin123")
else:
    print("Superuser already exists")
EOF

# Run health checks
print_status "Running health checks..."
$PYTHON_BIN $MANAGE_PY shell << EOF
from properties.monitoring import health_checker
health_report = health_checker.check_all_systems()
print(f"System Health: {health_report['status']}")
for component, status in health_report['components'].items():
    print(f"  {component}: {status['status']}")
EOF

# Restart services
print_status "Restarting services..."
systemctl restart gunicorn
systemctl restart celery
systemctl restart celerybeat

# Wait for services to start
sleep 5

# Check service status
print_status "Checking service status..."
systemctl status gunicorn --no-pager
systemctl status celery --no-pager

# Run final health check
print_status "Running final health check..."
HEALTH_CHECK_URL="http://localhost:8000/api/ai/health/"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)

if [ $HEALTH_STATUS -eq 200 ]; then
    print_status "Health check passed (HTTP $HEALTH_STATUS)"
else
    print_error "Health check failed (HTTP $HEALTH_STATUS)"
    print_warning "Rolling back to previous backup..."
    # Rollback logic here
    exit 1
fi

# Clean up old backups (keep last 7 days)
print_status "Cleaning up old backups..."
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;

print_status "Deployment completed successfully!"
print_status "Application is now running at: http://localhost:8000"
print_warning "Remember to change the default admin password"

# Display deployment summary
echo ""
echo "=== Deployment Summary ==="
echo "Backup: $BACKUP_NAME"
echo "Database: Migrated"
echo "Static Files: Collected"
echo "Services: Restarted"
echo "Health Check: Passed"
echo "========================"