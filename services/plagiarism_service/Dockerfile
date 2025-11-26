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

# Copy all services (needed for client imports)
COPY services/ ./services/

# Copy .env file if it exists (from GitHub Actions CI/CD)
COPY .env /app/ 2>/dev/null || true

# Set Python path to include the app root
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8003

# Run the service
CMD ["uvicorn", "services.plagiarism_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
