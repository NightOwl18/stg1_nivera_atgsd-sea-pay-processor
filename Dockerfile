FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Ensure Python can import the "app" package
ENV PYTHONPATH="/app"

# Install system libs
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into container
COPY . .

EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
  python - << 'EOF' \
import urllib.request; \
urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3) \
EOF

# Run the web application
CMD ["python", "/app/app/web.py"]
