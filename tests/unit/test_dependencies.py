from unittest.mock import MagicMock, patch

import pytest

from app import dependencies


@pytest.fixture(autouse=True)
def reset_dependencies():
    # Reset before each test
    dependencies._embedding_model = None
    dependencies._vector_store = None
    dependencies._query_service = None
    dependencies._ingestion_service = None
    dependencies._feedback_service = None
    yield
    # Reset after each test
    dependencies._embedding_model = None
    dependencies._vector_store = None
    dependencies._query_service = None
    dependencies._ingestion_service = None
    dependencies._feedback_service = None

def test_uninitialized_services_raise_errors():
    with pytest.raises(RuntimeError, match="QueryService is not initialized."):
        dependencies.get_query_service()
        
    with pytest.raises(RuntimeError, match="IngestionService is not initialized."):
        dependencies.get_ingestion_service()
        
    with pytest.raises(RuntimeError, match="FeedbackService is not initialized."):
        dependencies.get_feedback_service()

def test_initialized_services():
    dependencies._query_service = MagicMock()
    dependencies._ingestion_service = MagicMock()
    dependencies._feedback_service = MagicMock()
    
    assert dependencies.get_query_service() is not None
    assert dependencies.get_ingestion_service() is not None
    assert dependencies.get_feedback_service() is not None

@patch('app.dependencies.CrossEncoderReranker')
@patch('app.dependencies.SentenceTransformerAdapter')
@patch('app.dependencies.ChromaVectorStore')
@patch('app.dependencies.get_llm_client')
@patch('app.dependencies.build_rag_graph')
def test_initialize_services(mock_build_rag, mock_get_llm, mock_chroma, mock_sentence, mock_reranker):
    # Instead of running it in the module namespace which might be messed up by conftest,
    # we just verify that it doesn't crash when executed with mocked dependencies.
    import importlib

    import app.dependencies as fresh_deps
    importlib.reload(fresh_deps)
    
    with patch.object(fresh_deps, 'SentenceTransformerAdapter', mock_sentence), \
         patch.object(fresh_deps, 'ChromaVectorStore', mock_chroma), \
         patch.object(fresh_deps, 'CrossEncoderReranker', mock_reranker), \
         patch.object(fresh_deps, 'get_llm_client', mock_get_llm), \
         patch.object(fresh_deps, 'build_rag_graph', mock_build_rag):
        
        fresh_deps.initialize_services()
        
        assert fresh_deps.get_query_service() is not None
        assert fresh_deps.get_ingestion_service() is not None
        assert fresh_deps.get_feedback_service() is not None
