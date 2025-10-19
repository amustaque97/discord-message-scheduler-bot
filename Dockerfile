# Discord Message Scheduler Bot - Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY bot.py .
COPY config.py .
COPY appwrite_client.py .
COPY scheduler_service.py .
COPY setup_appwrite.py .
COPY commands/ ./commands/

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check (optional - checks if bot.log is being updated)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD test -f /app/bot.log && test $(($(date +%s) - $(stat -c %Y /app/bot.log))) -lt 300 || exit 1

# Run the bot
CMD ["python", "-u", "bot.py"]

