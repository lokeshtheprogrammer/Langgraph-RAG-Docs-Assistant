import sqlite3
from datetime import datetime

import pytest

from app.core.exceptions import DatabaseError
from app.repositories.document_repository import DocumentRepository
from app.repositories.feedback_repository import FeedbackRepository


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create document table
    conn.execute('''
        CREATE TABLE documents (
            id TEXT PRIMARY KEY,
            filename TEXT,
            source_url TEXT,
            file_hash TEXT,
            file_size_bytes INTEGER,
            file_type TEXT,
            chunk_count INTEGER,
            status TEXT,
            ingestion_timestamp TEXT,
            embedding_model TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create feedback table
    conn.execute('''
        CREATE TABLE feedback (
            feedback_id TEXT PRIMARY KEY,
            query TEXT,
            answer TEXT,
            rating TEXT,
            comment TEXT,
            sources_used TEXT,
            session_id TEXT,
            query_type TEXT,
            retry_count INTEGER,
            response_time_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_document_repository(memory_db):
    doc = {
        "id": "doc_1",
        "filename": "test.md",
        "source_url": "test.md",
        "file_hash": "hash123",
        "file_size_bytes": 100,
        "file_type": "text/markdown",
        "chunk_count": 5,
        "status": "completed",
        "ingestion_timestamp": datetime.utcnow().isoformat(),
        "embedding_model": "test_model",
        "error_message": None
    }
    
    # Test Insert
    DocumentRepository.insert_document(memory_db, doc)
    
    # Test Get by ID
    retrieved = DocumentRepository.get_document_by_id(memory_db, "doc_1")
    assert retrieved is not None
    assert retrieved["filename"] == "test.md"
    
    # Test Get by Hash
    retrieved_hash = DocumentRepository.get_document_by_hash(memory_db, "hash123")
    assert retrieved_hash is not None
    assert retrieved_hash["id"] == "doc_1"
    
    # Test List
    docs = DocumentRepository.list_documents(memory_db)
    assert len(docs) == 1
    
    docs_completed = DocumentRepository.list_documents(memory_db, status="completed")
    assert len(docs_completed) == 1
    
    # Test Count
    assert DocumentRepository.count_documents(memory_db) == 1
    assert DocumentRepository.count_documents(memory_db, status="completed") == 1
    
    # Test Update Status
    DocumentRepository.update_document_status(memory_db, "doc_1", "failed", 0, "error")
    updated = DocumentRepository.get_document_by_id(memory_db, "doc_1")
    assert updated["status"] == "failed"
    assert updated["error_message"] == "error"
    
    # Test Delete
    DocumentRepository.delete_document(memory_db, "doc_1")
    assert DocumentRepository.get_document_by_id(memory_db, "doc_1") is None

def test_document_repository_errors(memory_db):
    memory_db.execute("DROP TABLE documents")
    with pytest.raises(DatabaseError):
        DocumentRepository.insert_document(memory_db, {"id": "doc_1"})
    with pytest.raises(DatabaseError):
        DocumentRepository.list_documents(memory_db)
    with pytest.raises(DatabaseError):
        DocumentRepository.count_documents(memory_db)
    with pytest.raises(DatabaseError):
        DocumentRepository.get_document_by_id(memory_db, "doc_1")
    with pytest.raises(DatabaseError):
        DocumentRepository.get_document_by_hash(memory_db, "hash123")
    with pytest.raises(DatabaseError):
        DocumentRepository.delete_document(memory_db, "doc_1")
    with pytest.raises(DatabaseError):
        DocumentRepository.update_document_status(memory_db, "doc_1", "failed")

def test_feedback_repository(memory_db):
    feedback = {
        "feedback_id": "fb_1",
        "query": "test query",
        "answer": "test answer",
        "rating": "positive",
        "comment": "good",
        "sources_used": ["source1"],
        "session_id": "session1",
        "query_type": "rag",
        "retry_count": 0,
        "response_time_ms": 150.0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Test Insert
    FeedbackRepository.insert_feedback(memory_db, feedback)
    
    # Test List
    feedbacks = FeedbackRepository.list_feedback(memory_db)
    assert len(feedbacks) == 1
    assert "source1" in feedbacks[0]["sources_used"] # test json parsing
    
    feedbacks_positive = FeedbackRepository.list_feedback(memory_db, rating="positive")
    assert len(feedbacks_positive) == 1
    
    # Test Count
    assert FeedbackRepository.count_feedback(memory_db) == 1
    assert FeedbackRepository.count_feedback(memory_db, rating="positive") == 1

def test_feedback_repository_errors(memory_db):
    memory_db.execute("DROP TABLE feedback")
    with pytest.raises(DatabaseError):
        FeedbackRepository.insert_feedback(memory_db, {"feedback_id": "fb_1"})
    with pytest.raises(DatabaseError):
        FeedbackRepository.list_feedback(memory_db)
    with pytest.raises(DatabaseError):
        FeedbackRepository.count_feedback(memory_db)
