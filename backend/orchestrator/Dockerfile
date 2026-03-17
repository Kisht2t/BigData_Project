FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY backend/orchestrator/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules onto the Python path
COPY backend/shared /app/shared
COPY backend/worker /app/worker

# Copy orchestrator service code
COPY backend/orchestrator /app/orchestrator

ENV PYTHONPATH="/app:/app/worker"
WORKDIR /app/orchestrator

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
