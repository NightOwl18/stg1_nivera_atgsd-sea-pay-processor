FROM python:3.12-slim

WORKDIR /app

# Install system deps if needed later (poppler, fonts, etc.)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Flask settings
ENV FLASK_ENV=production
EXPOSE 8080

CMD ["python", "-m", "app.web"]
