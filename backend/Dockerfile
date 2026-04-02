# ── Stage 1: Builder ──────────────────────────────
FROM python:3.11-slim AS builder

# Intel Mac x86_64 compatibility
# This image works on both Intel Mac and Linux x86_64
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (layer caching)
COPY pyproject.toml ./

# Install dependencies to isolated location
RUN pip install --no-cache-dir --prefix=/install \
    --extra-index-url https://pypi.org/simple \
    ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir --prefix=/install .

# ── Stage 2: Runtime ──────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system deps only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user (security)
RUN groupadd -r pavlov && \
    useradd -r -g pavlov -d /app -s /bin/bash pavlov

# Copy application code
COPY --chown=pavlov:pavlov app/ ./app/
COPY --chown=pavlov:pavlov alembic/ ./alembic/
COPY --chown=pavlov:pavlov alembic.ini ./

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root
USER pavlov

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health \
        || exit 1

EXPOSE 8000

# Entrypoint: migrate then start
CMD ["sh", "-c", \
    "alembic upgrade head && \
     uvicorn app.main:app \
     --host  0.0.0.0 \
     --port 8000 \
     --workers 1 \
     --log-level info"]