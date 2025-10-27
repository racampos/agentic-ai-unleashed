# AI Networking Lab Tutor API - Dockerfile
# This containerizes the FastAPI backend with LangGraph orchestrator

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Include all Python packages: api, orchestrator, simulator, config
COPY api/ ./api/
COPY orchestrator/ ./orchestrator/
COPY simulator/ ./simulator/
COPY config/ ./config/
COPY data/ ./data/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
