# Stage 1: Build
# Force rebuild - 2026-09-11 - Fix file copying to ensure all project files are included
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

# Copy application code
COPY . .

# Copy entrypoint script
RUN chmod +x /app/entrypoint.sh

# Create static files directory
RUN mkdir -p staticfiles media static

# Expose port - Railway uses PORT environment variable (standard is 8080)
EXPOSE 8080

# Run application
CMD ["/app/entrypoint.sh"]