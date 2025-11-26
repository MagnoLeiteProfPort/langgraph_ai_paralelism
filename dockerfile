# ==========================================
# Base image
# ==========================================
FROM python:3.11-slim AS base

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# ==========================================
# System deps (optional: build tools if needed)
# ==========================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# Python dependencies
# ==========================================
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Application code
# ==========================================
COPY . .

# ==========================================
# Default command
# ==========================================
# main.py is the entrypoint for the workflow
CMD ["python", "main.py"]
