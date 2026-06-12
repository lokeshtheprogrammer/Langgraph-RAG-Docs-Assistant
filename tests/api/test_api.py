import io

from app.workflow.state import DocumentChunk


# 1. Test GET /health
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["vector_store"] == "ok"
    assert data["components"]["document_registry"] == "ok"

# 2. Test POST /query
def test_query_assistant(client, test_vector_store, mock_embeddings):
    # Add mock chunk to the vector store so retrieval succeeds
    mock_chunk = DocumentChunk(
        content="FastAPI is a modern web framework.",
        source_file="fastapi.md",
        document_id="doc_fastapi",
        chunk_index=0
    )
    test_vector_store.add_chunks([mock_chunk], mock_embeddings.embed_documents([mock_chunk.content]))

    payload = {
        "question": "What is FastAPI?",
        "session_id": "12345678-1234-5678-1234-567812345678"
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert data["answer"] == "FastAPI is a modern web framework."

def test_query_validation_errors(client):
    # Empty query
    response = client.post("/query", json={"question": ""})
    assert response.status_code == 422 # Pydantic min_length validation raises 422
    assert "detail" in response.json() or "error" in response.json()

    # Too long query
    response = client.post("/query", json={"question": "a" * 2001})
    assert response.status_code == 422
    assert "detail" in response.json() or "error" in response.json()

    # Invalid UUID session_id format
    response = client.post("/query", json={"question": "What is FastAPI?", "session_id": "invalid-uuid"})
    assert response.status_code == 422
    assert "detail" in response.json() or "error" in response.json()

# 3. Test POST /ingest
def test_ingest_document_validation(client):
    # Neither URL nor file
    # We pass an empty files dict to force multipart encoding
    response = client.post("/ingest", files={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Both URL and file
    file_data = ("test.txt", io.BytesIO(b"Hello world"))
    response = client.post(
        "/ingest",
        files={
            "url": (None, "http://example.com"),
            "file": file_data
        }
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid URL scheme
    response = client.post("/ingest", files={"url": (None, "ftp://example.com")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid file extension
    file_data = ("test.exe", io.BytesIO(b"Hello world"))
    response = client.post("/ingest", files={"file": file_data})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_ingest_url_success(client):
    response = client.post("/ingest", files={"url": (None, "https://fastapi.tiangolo.com/")})
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "indexed"

def test_ingest_file_success(client):
    file_data = ("sample.md", io.BytesIO(b"# Sample Header\nTest file content."))
    response = client.post("/ingest", files={"file": file_data})
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "indexed"

# 4. Test GET /documents
def test_list_indexed_documents(client):
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

# 5. Test POST /feedback
def test_submit_feedback(client):
    feedback_payload = {
        "query": "What is FastAPI?",
        "answer": "FastAPI is a modern web framework.",
        "rating": "thumbs_up",
        "comment": "Super helpful!",
        "session_id": "12345678-1234-5678-1234-567812345678"
    }
    response = client.post("/feedback", json=feedback_payload)
    assert response.status_code == 200
    data = response.json()
    assert "feedback_id" in data
    assert data["status"] == "recorded"

def test_list_feedback(client):
    # Submit one feedback first
    feedback_payload = {
        "query": "What is FastAPI?",
        "answer": "FastAPI is a modern web framework.",
        "rating": "thumbs_down",
        "comment": "Not what I expected.",
        "session_id": "12345678-1234-5678-1234-567812345678"
    }
    client.post("/feedback", json=feedback_payload)

    # Get list
    response = client.get("/feedback?rating=thumbs_down")
    assert response.status_code == 200
    data = response.json()
    assert "feedback" in data
    assert len(data["feedback"]) > 0
    assert data["feedback"][0]["rating"] == "thumbs_down"

# 6. Test DELETE /documents/{id}
def test_delete_document(client):
    # Ingest a document first to delete it
    file_data = ("todelete.md", io.BytesIO(b"# To Delete\nContent to delete."))
    ingest_res = client.post("/ingest", files={"file": file_data})
    doc_id = ingest_res.json()["document_id"]

    # Delete it
    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

# 7. Test conversational query
def test_conversational_query(client, mock_llm_client):
    # Setup mock LLM responses specifically for this test
    mock_llm_client.responses = {
        "Classify the query type": '{"rewritten_query": "Hello", "query_type": "conversational"}',
        "The user is greeting you": "Hello! I am your Technical Documentation Copilot. How can I help you today?"
    }
    
    payload = {
        "question": "Hello!",
        "session_id": "12345678-1234-5678-1234-567812345678"
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "Hello! I am your Technical Documentation Copilot." in data["answer"]
    assert len(data["sources"]) == 0

