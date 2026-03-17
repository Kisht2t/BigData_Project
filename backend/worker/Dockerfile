FROM python:3.12-slim

WORKDIR /app

# Install dependencies (sentence-transformers is the heavy one)
COPY backend/worker/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at build time (baked into image, no runtime download)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy shared modules onto the Python path
COPY backend/shared /app/shared

# Copy worker service code
COPY backend/worker /app/worker

ENV PYTHONPATH="/app"
WORKDIR /app/worker

CMD ["python", "main.py"]
