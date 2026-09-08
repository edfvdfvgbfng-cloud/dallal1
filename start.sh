#!/bin/bash
# Railway startup script - uses entrypoint.sh for proper production setup
echo "Starting Django application via entrypoint.sh..."
chmod +x entrypoint.sh
./entrypoint.sh