FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy application code (will be overridden by volume mount in dev)
COPY app /app/app

EXPOSE 8000

ENTRYPOINT ["tini", "--"]
# Enable hot reload with --reload flag for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
