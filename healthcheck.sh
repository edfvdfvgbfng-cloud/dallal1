#!/bin/bash
PORT=${PORT:-8000}
curl -f http://localhost:$PORT/health/ || exit 1
