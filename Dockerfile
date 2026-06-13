FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install system dependencies needed for compiling certain python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer embedding model to cache it in the Docker image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code and folders
COPY app/ ./app/
COPY corpus/ ./corpus/
COPY ingestion/ ./ingestion/
COPY streamlit_app.py .
COPY .streamlit/ ./.streamlit/
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Create persistent storage directories
RUN mkdir -p /app/data /app/chroma_db

# Expose port (Hugging Face default is 7860)
EXPOSE 7860

# Run start script
CMD ["bash", "start.sh"]
