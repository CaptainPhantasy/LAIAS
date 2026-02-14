# LAIAS Docker Orchestrator - Production Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Builder
FROM python:3.11-slim AS builder

LABEL maintainer="LAIAS Platform"
LABEL description="Builder stage for docker-orchestrator"
LABEL stage="builder"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

LABEL maintainer="LAIAS Platform"
LABEL description="Docker container lifecycle management for LAIAS agents"
LABEL version="1.0.0"

# Install runtime dependencies
# Note: docker CLI is NOT needed - we mount host socket
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash laias && \
    mkdir -p /app /var/laias/agents && \
    chown -R laias:laias /app /var/laias

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
WORKDIR /app
COPY app ./app

# Note: Running as root to access Docker socket
# In production, consider using TLS or rootless Docker

# Expose port (API_PORT from config)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8002", \
     "--workers", "1"]
