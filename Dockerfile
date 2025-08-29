FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
COPY README.md ./

# Copy source code
COPY src/ ./src/
COPY healthcheck.py ./

# Install Python package
RUN pip install --no-cache-dir .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create data and logs directories with proper permissions
RUN mkdir -p /data /logs && \
    chown -R appuser:appuser /app /data /logs && \
    chmod -R 755 /data /logs

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

# Health check - actually tests bot connectivity to Telegram API
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py

# Run the bot
CMD ["appeals-bot"]
