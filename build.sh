#!/usr/bin/env bash
set -o errexit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:/app:/workspace:$PYTHONPATH"

pip install -r requirements.txt
mkdir -p staticfiles logs media static

python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
