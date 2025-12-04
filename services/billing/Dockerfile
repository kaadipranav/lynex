FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy shared code and libs
COPY libs /app/libs
COPY services/shared /app/services/shared

# Copy service code
COPY services/billing /app/services/billing

# Install dependencies
WORKDIR /app/services/billing
RUN pip install --no-cache-dir -r requirements.txt

# Install internal SDK
RUN pip install -e /app/libs/sdk-python

# Set Python path to include root for shared imports
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
