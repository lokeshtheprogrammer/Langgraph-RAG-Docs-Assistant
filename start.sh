#!/bin/bash
# Start FastAPI backend in the background
echo "Starting FastAPI backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start up
echo "Waiting for API to initialize..."
sleep 5

# Index the document corpus
echo "Seeding Vector Database..."
python ingestion/ingest_corpus.py

# Start Streamlit UI on port 7860 (Hugging Face default)
echo "Starting Streamlit UI..."
streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0 --server.enableXsrfProtection false
