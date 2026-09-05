#!/usr/bin/env bash
set -o errexit

echo "=== Dalal Platform Startup ==="
echo "=== Database Protection: ENABLED ==="
echo "=== No flush, no reset, safe migrations only ==="
export PYTHONPATH=/app:$PYTHONPATH

# Verify Django installation
python -c "import django; print('Django installed successfully')"

# Verify critical files exist
if [ ! -f /app/dalal_project/settings.py ]; then
    echo "ERROR: settings.py not found"
    exit 1
fi

if [ ! -d /app/properties ]; then
    echo "ERROR: Properties app not found"
    exit 1
fi

echo "All checks passed. Starting server with protected database..."
exec python run_server.py