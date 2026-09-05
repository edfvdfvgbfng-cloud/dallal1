#!/usr/bin/env bash
set -o errexit

echo "=== Dalal Platform Startup ==="
echo "=== Database Protection: ENABLED ==="
echo "=== No flush, no reset, safe migrations only ==="

# Set working directory and comprehensive PYTHONPATH
cd /app
export PYTHONPATH=/app:/app/dalal_project:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=dalal_project.settings

# Debug logging
echo "Working directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "Python version: $(python --version)"
echo "=== Directory Structure ==="
ls -la /app/
echo "=== dalal_project directory ==="
ls -la /app/dalal_project/ || echo "dalal_project directory NOT FOUND"

# Verify Django installation
python -c "import django; print('Django installed:', django.__version__)" || exit 1

# Verify project structure
if [ ! -f /app/dalal_project/settings.py ]; then
    echo "ERROR: settings.py not found in /app/dalal_project"
    exit 1
fi

if [ ! -d /app/properties ]; then
    echo "ERROR: Properties app not found in /app"
    exit 1
fi

# Verify dalal_project can be imported with explicit path
python -c "import sys; sys.path.insert(0, '/app'); import dalal_project; print('dalal_project package found OK')" || \
    (echo "ERROR: dalal_project import failed" && python -c "import sys; print('Python path:', sys.path)" && exit 1)

echo "All system checks passed. Starting server with protected database..."
exec python run_server.py
