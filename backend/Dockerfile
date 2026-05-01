# Multi-stage Dockerfile for AETHER-SCORE Backend
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Default port (Render will override with $PORT)
ENV PORT=4000

# Switch to non-root user
USER appuser

# Expose port (Render will map $PORT to this)
EXPOSE 4000

# Health check - use $PORT environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "curl -f http://localhost:${PORT:-4000}/health || exit 1"

# Run the application - use shell form to expand $PORT
# Use $PORT if set (Render provides this), otherwise default to 4000
# Use --workers 1 for Render (single process, Render handles scaling)
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-4000} --workers 1


