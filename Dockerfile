# Simplified Dockerfile for Railway deployment
# Force rebuild - 2026-09-14-16-00 - Fix missing manage.py issue
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    python3-dev \
    libpq-dev \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy all application files at once
COPY . .

# Make scripts executable
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true
RUN chmod +x /app/start.sh 2>/dev/null || true

# Create static files directory
RUN mkdir -p staticfiles media static

# Debug: show what was copied
RUN ls -la /app
RUN echo "Checking for manage.py:"
RUN test -f /app/manage.py && echo "manage.py found" || echo "manage.py NOT found"

# Expose port - Railway uses PORT environment variable (standard is 8080)
EXPOSE 8080

# Run application
CMD ["/app/entrypoint.sh"]