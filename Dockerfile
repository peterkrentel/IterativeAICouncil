FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent scripts
COPY agents/ ./agents/

# Create ai directory for mounted volume
RUN mkdir -p /app/ai

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AI_DIR=/app/ai

# Make orchestrator executable
RUN chmod +x /app/agents/orchestrator.py

# Default command runs the orchestrator
CMD ["python", "/app/agents/orchestrator.py"]
