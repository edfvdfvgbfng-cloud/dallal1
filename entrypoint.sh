#!/usr/bin/env bash
set -o errexit

# Force Railway redeploy - 2026-08-24-15-25 - Simplified startup
echo "=== Dalal Platform Startup ==="
export PYTHONPATH=/app:$PYTHONPATH

# Check if Django is installed
python -c "import django; print('Django installed successfully')"

# Check if settings.py exists
if [ -f /app/dalal_project/settings.py ]; then
    echo "Settings.py found"
else
    echo "ERROR: settings.py not found"
fi

# Check if properties app exists
if [ -d /app/properties ]; then
    echo "Properties app exists"
else
    echo "ERROR: Properties app not found"
fi

echo "Starting server..."
exec python run_server.py