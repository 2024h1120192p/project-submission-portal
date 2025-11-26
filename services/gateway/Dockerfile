# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libs
COPY libs/ ./libs/

# Copy config
COPY config/ ./config/

# Copy all services (gateway needs to import clients from other services)
COPY services/ ./services/

# Copy .env file if it exists (from GitHub Actions CI/CD)
COPY .env /app/

# Set Python path to include the app root
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "services.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
