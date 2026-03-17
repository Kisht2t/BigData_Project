FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY ingestion/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy shared and worker modules onto the Python path
COPY backend/shared /app/shared
COPY backend/worker /app/worker

# Copy ingestion pipeline code
COPY ingestion /app/ingestion

ENV PYTHONPATH="/app:/app/worker"
WORKDIR /app/ingestion

CMD ["python", "pipeline.py"]
