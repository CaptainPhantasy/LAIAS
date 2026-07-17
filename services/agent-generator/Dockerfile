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

# Switched 2026-04-29 from python:3.11-slim → python:3.13-slim so the
# constraints.txt (frozen from a working python3.13 venv) installs without
# wheel-incompatibility fallbacks. CrewAI 1.x and its transitive deps no
# longer publish 3.11 wheels for several packages (pandas 3.0.0, numpy
# 2.4.2, etc.); 3.13 also fixes the multi-minute pip backtracking storm
# the prior loose deps caused.
FROM python:3.13-slim

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
# Constraints come from a known-working venv (services/agent-generator/venv,
# python3.13). Without `-c constraints.txt` pip walks through dozens of
# versions of crewai-tools, composio, instructor, transformers, and
# opentelemetry trying to satisfy the loose `>=` floors in requirements.txt;
# the build hangs ≥ 14 min and never converges. With constraints, pip
# resolves on the first pass.
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -c constraints.txt -r requirements.txt

# === Application Code ===
COPY app/ ./app/

RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app

# === Health Check ===
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# === Expose Port ===
EXPOSE 8001

# === Environment Variables ===
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO

USER appuser

# === Run Command ===
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
