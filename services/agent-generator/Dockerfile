# =============================================================================
# LAIAS Agent Generator - Dockerfile
# =============================================================================
#
# FastAPI service that uses LLMs to generate production-ready
# CrewAI agent code from natural language descriptions.
#
# Build: docker build -t laias/agent-generator:latest .
# Run:   docker run -p 8001:8001 --env-file .env laias/agent-generator
#
# =============================================================================

FROM python:3.11-slim

LABEL maintainer="LAIAS Platform"
LABEL description="Agent Generator Service - LLM-powered CrewAI code generator"
LABEL version="1.0.0"

# === System Dependencies ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# === Working Directory ===
WORKDIR /app

# === Python Dependencies ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Application Code ===
COPY app/ ./app/

# === Health Check ===
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# === Expose Port ===
EXPOSE 8001

# === Environment Variables ===
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO

# === Run Command ===
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
