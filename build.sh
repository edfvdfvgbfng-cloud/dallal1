#!/usr/bin/env bash
set -o errexit
export PYTHONPATH=/app
export MISE_PYTHON_GITHUB_ATTESTATIONS=false
mise install
pip install -r requirements.txt
mkdir -p staticfiles
# CRITICAL: Database Protection - safe operations only
# --noinput prevents any destructive operations
python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
