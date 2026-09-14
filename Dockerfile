# Stage 1: Build
# Force rebuild - 2026-09-14 - Fix file copying to ensure all project files are included
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install gunicorn in runtime if not copied
RUN pip install gunicorn

# Copy application code - explicit copy to ensure manage.py is at /app
COPY manage.py /app/manage.py
COPY requirements.txt /app/requirements.txt
COPY dalal_project /app/dalal_project
COPY templates /app/templates
COPY static /app/static
COPY assets /app/assets
COPY properties /app/properties
COPY scripts /app/scripts
COPY entrypoint.sh /app/entrypoint.sh
COPY start.sh /app/start.sh
COPY create_admin_user.py /app/create_admin_user.py
COPY *.md /app/

# Copy entrypoint script
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/start.sh

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