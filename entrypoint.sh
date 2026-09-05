#!/usr/bin/env bash
set -o errexit

echo "=== Dalal Platform Startup ==="
echo "=== Database Protection: ENABLED ==="
echo "=== No flush, no reset, safe migrations only ==="

# Set working directory and comprehensive PYTHONPATH
cd /app
export PYTHONPATH=/app:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=dalal_project.settings

# Verify Python path
echo "PYTHONPATH: $PYTHONPATH"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

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

# Verify dalal_project can be imported
python -c "import sys; sys.path.insert(0, '/app'); import dalal_project; print('dalal_project package found OK')" || exit 1

echo "All system checks passed. Starting server with protected database..."
exec python run_server.py
