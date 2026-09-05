#!/usr/bin/env bash
set -o errexit

echo "=== Dalal Platform Startup ==="
echo "=== Database Protection: ENABLED ==="
echo "=== No flush, no reset, safe migrations only ==="

# Set working directory and comprehensive PYTHONPATH
cd /app
export PYTHONPATH=/app:/app/dalal_project:$PYTHONPATH

# Verify Django installation and dalal_project import
python -c "import django; print('Django installed:', django.__version__)"
python -c "import dalal_project; print('dalal_project package found OK')"

# Verify critical files exist
if [ ! -f /app/dalal_project/settings.py ]; then
    echo "ERROR: settings.py not found in /app/dalal_project"
    exit 1
fi

if [ ! -d /app/properties ]; then
    echo "ERROR: Properties app not found in /app"
    exit 1
fi

echo "All system checks passed. Starting server with protected database..."
exec python run_server.py
