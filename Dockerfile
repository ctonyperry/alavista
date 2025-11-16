# Alavista Application Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY alavista/ ./alavista/
COPY tests/ ./tests/

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data

# Default command runs tests
CMD ["pytest", "-v"]
