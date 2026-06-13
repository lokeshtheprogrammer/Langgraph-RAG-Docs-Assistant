import os
import shutil
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

import app.core.database as app_db
import app.dependencies as app_deps
import app.main as app_main
from app.config import settings
from app.core.database import get_db_connection
from app.dependencies import get_feedback_service, get_ingestion_service, get_query_service
from app.infrastructure.embeddings.base import EmbeddingModelBase
from app.infrastructure.llm.base import LLMClientBase
from app.infrastructure.vector_store.chroma import ChromaVectorStore
from app.main import app
from app.services.feedback_service import FeedbackService
from app.services.ingestion_service import IngestionService
from app.services.query_service import QueryService
from app.workflow.graph import build_rag_graph

# Ensure workspace root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create temp directories for testing to avoid polluting real database/chromadb directories
test_dir = tempfile.mkdtemp()
test_db_path = os.path.join(test_dir, "test_app.db")
test_chroma_path = os.path.join(test_dir, "test_chroma_db")

# Force settings properties before any app modules use them
settings.SQLITE_DB_PATH = test_db_path
settings.CHROMA_PERSIST_DIR = test_chroma_path
settings.LLM_PROVIDER = "google"
settings.LLM_MODEL = "gemini-2.5-flash"
settings.GEMINI_API_KEY = "mock_gemini_key"
settings.GROQ_API_KEY = "mock_groq_key"

# Stub out heavy startup service and database initialization
real_initialize_db = app_db.initialize_db
real_initialize_services = app_deps.initialize_services

app_deps.initialize_services = lambda: None
app_db.initialize_db = lambda: None
app_main.initialize_services = lambda: None
app_main.initialize_db = lambda: None


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the temp SQLite database schema for the test session."""
    real_initialize_db()
    yield
    # Cleanup temp directory after test session
    try:
        shutil.rmtree(test_dir)
    except Exception:
        pass


@pytest.fixture
def db_conn():
    """Provides a thread-safe connection to the test SQLite database."""
    with get_db_connection() as conn:
        yield conn


@pytest.fixture
def mock_llm_client():
    class MockLLM(LLMClientBase):
        def __init__(self):
            self.responses = {}
            self.calls = []
        async def ainvoke(self, messages: list[dict], **kwargs) -> str:
            self.calls.append(messages)
            prompt = messages[-1]["content"]
            for key, resp in self.responses.items():
                if key in prompt:
                    return resp
            # Default response structures
            if "Classify the query type" in prompt:
                return '{"rewritten_query": "What is FastAPI?", "query_type": "conceptual"}'
            elif "determine if the given document chunk is useful" in prompt:
                return '{"grade": "relevant"}'
            elif "You are a factual grounding checker" in prompt:
                return '{"score": 1.0, "supported": true, "unsupported_claims": []}'
            elif "Answer the user's question using ONLY" in prompt or "FAILED GROUNDING VERIFICATION" in prompt:
                return "FastAPI is a modern web framework."
            return "{}"
    return MockLLM()


@pytest.fixture
def mock_embeddings():
    class MockEmbeddings(EmbeddingModelBase):
        def embed_query(self, text: str) -> list[float]:
            return [0.1] * 384
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[0.1] * 384 for _ in texts]
    return MockEmbeddings()


@pytest.fixture
def test_vector_store():
    # Use real persistent store but pointing to temp chroma path
    return ChromaVectorStore(test_chroma_path)


@pytest.fixture
def client(mock_llm_client, mock_embeddings, test_vector_store):
    """Provides a TestClient for API endpoints with dependencies overridden."""
    # Build mock graph
    mock_graph = build_rag_graph(test_vector_store, mock_embeddings, mock_llm_client, web_search_client=None)
    
    # Instantiate mock services
    mock_query_service = QueryService(mock_graph)
    mock_ingestion_service = IngestionService(test_vector_store, mock_embeddings)
    mock_feedback_service = FeedbackService()
    
    # Register overrides
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    
    with TestClient(app) as tc:
        yield tc
        
    # Clear overrides after test
    app.dependency_overrides.clear()
