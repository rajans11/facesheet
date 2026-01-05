# Base image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (for Playwright & PDF tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    unzip \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libpango-1.0-0 \
    libcairo2 \
    libffi-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY ../requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright (with Chromium and all required deps)
RUN python -m playwright install --with-deps

# Copy application code
COPY app/ /app/
COPY templates/ /app/templates/

# Expose the app port
EXPOSE 8080

# Run app using Gunicorn
CMD ["gunicorn", "-w", "6", "-b", "0.0.0.0:8080", "--timeout", "300", "app:app"]
