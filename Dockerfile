# Build stage
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install pip-tools
RUN pip install --no-cache-dir pip-tools

# Copy requirements files
COPY requirements.txt requirements.in ./

# Create wheels directory and build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5000

# Run the application with gunicorn
# Using 4 workers as a reasonable default (adjust based on your needs)
# --access-logfile - sends access logs to stdout
# --error-logfile - sends error logs to stderr
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "backend.wsgi:app"]

