#!/usr/bin/env bash
set -o errexit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:/app:/workspace:$PYTHONPATH"

echo "=== Dalal Platform Startup ==="
echo "PORT=${PORT:-8080}"
echo "DEBUG=${DEBUG:-False}"
echo "PYTHONPATH=$PYTHONPATH"

python run_server.py
