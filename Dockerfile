# Base image with Python already installed
FROM python:3.13-slim

# Do not create .pyc files and show logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/students.db

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and tests
COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .

# Folder for the SQLite database (a Docker volume is mounted here)
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# The API listens on port 8000 inside the container
EXPOSE 8000

# Docker marks the container healthy when /health responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 0.0.0.0 makes the server reachable from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
