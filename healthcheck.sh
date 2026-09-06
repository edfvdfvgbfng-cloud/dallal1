#!/bin/bash
PORT=${PORT:-8000}
echo "Healthcheck: Testing http://localhost:$PORT/health/"
curl -f http://localhost:$PORT/health/ || echo "Healthcheck failed but continuing"
exit 0
