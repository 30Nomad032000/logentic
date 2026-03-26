# ============================================================
# Voice Assistant - Multi-stage Docker Build
# Edge-optimized container for the multilingual voice assistant
# ============================================================

# ---- Stage 1: Builder ----
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.10-slim AS runtime

LABEL maintainer="Ebin John Joseph"
LABEL description="Hyper-Localized Multilingual Voice Assistant"
LABEL version="0.2.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy frontend build (if exists)
COPY frontend/dist/ ./frontend/dist/ 2>/dev/null || true

# Create directories for runtime data
RUN mkdir -p /app/data /app/models /app/reports

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MODEL_CACHE_DIR=/app/models
ENV HF_HOME=/app/models/huggingface

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
