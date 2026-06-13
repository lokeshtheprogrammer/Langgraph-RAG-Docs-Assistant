import asyncio
import os
import shutil
import sys

import httpx

# Ensure workspace root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def reset_storage():
    print("=== Resetting Storage ===")
    
    # 1. Delete SQLite db
    db_path = settings.SQLITE_DB_PATH
    if os.path.exists(db_path):
        print(f"Deleting SQLite database: {db_path}")
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Warning: Could not remove database file: {e}")
        
    # 2. Delete ChromaDB persist folder
    chroma_dir = settings.CHROMA_PERSIST_DIR
    if os.path.exists(chroma_dir):
        print(f"Deleting ChromaDB directory: {chroma_dir}")
        try:
            shutil.rmtree(chroma_dir)
        except Exception as e:
            print(f"Warning: Could not remove ChromaDB directory: {e}")
        
    print("Storage reset complete.\n")

def run_seed_script():
    print("=== Running Seed/Ingestion Script ===")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "ingestion.ingest_corpus"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("ERROR: Ingestion seed script failed!")
        print(result.stderr)
        sys.exit(1)
    print("Ingestion seed script ran successfully.\n")

async def run_smoke_test():
    print("=== Running Smoke Test Queries against API ===")
    url = "http://127.0.0.1:8000"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            health_res = await client.get(f"{url}/health")
            print(f"GET /health status: {health_res.status_code}")
            print(health_res.json())
            
            # Run queries
            queries = [
                "What is FastAPI?",
                "What is Pydantic?",
                "What is LangGraph?"
            ]
            
            for query in queries:
                query_payload = {
                    "question": query,
                    "session_id": "12345678-1234-5678-1234-567812345678"
                }
                print("\n" + "-"*40)
                print(f"Querying: {query}...")
                print("-"*40)
                
                query_res = await client.post(f"{url}/query", json=query_payload)
                print(f"POST /query status: {query_res.status_code}")
                if query_res.status_code != 200:
                    print(f"Error Response: {query_res.text}")
                    continue
                    
                res_json = query_res.json()
                print("Generated Answer:")
                print(res_json.get("answer"))
                print("\nSources Cited:")
                for src in res_json.get("sources", []):
                    print(f" - {src['source_file']} (Excerpt: '{src['excerpt']}')")
                print(f"Grounding Checked: {not res_json.get('is_fallback')}")
                
        except Exception as e:
            print(f"API request failed: {e}")
            print("Is the FastAPI server running on port 8000?")
            sys.exit(1)

if __name__ == "__main__":
    # If server is running, we might not be able to delete the DB due to open connection handles.
    # We will try, but if it fails it's okay because uvicorn is running.
    reset_storage()
    run_seed_script()
    asyncio.run(run_smoke_test())
