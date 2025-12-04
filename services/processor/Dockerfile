FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy shared code and libs
COPY libs /app/libs
COPY services/shared /app/services/shared

# Copy service code
COPY services/processor /app/services/processor

# Install dependencies
WORKDIR /app/services/processor
RUN pip install --no-cache-dir -r requirements.txt

# Install internal SDK
RUN pip install -e /app/libs/sdk-python

# Set Python path to include root for shared imports
ENV PYTHONPATH=/app

# Run application
CMD ["python", "main.py"]

