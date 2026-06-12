
from app.config import settings
from app.core.logging import logger
from app.infrastructure.embeddings.sentence_transformers import SentenceTransformerAdapter
from app.infrastructure.llm.adapters import get_llm_client
from app.infrastructure.vector_store.chroma import ChromaVectorStore
from app.infrastructure.web_search.adapters import get_web_search_client
from app.services.feedback_service import FeedbackService
from app.services.ingestion_service import IngestionService
from app.services.query_service import QueryService
from app.workflow.graph import build_rag_graph

# Singletons initialized on startup
_embedding_model: SentenceTransformerAdapter | None = None
_vector_store: ChromaVectorStore | None = None
_query_service: QueryService | None = None
_ingestion_service: IngestionService | None = None
_feedback_service: FeedbackService | None = None

def initialize_services():
    """Build and compile all service singletons at API application startup."""
    global _embedding_model, _vector_store, _query_service, _ingestion_service, _feedback_service
    logger.info("Initializing application services singletons...")
    
    # 1. Embeddings & Vector store
    _embedding_model = SentenceTransformerAdapter(settings.EMBEDDING_MODEL)
    _vector_store = ChromaVectorStore(settings.CHROMA_PERSIST_DIR)
    
    # 2. LLM Provider
    llm_client = get_llm_client(settings.LLM_PROVIDER, settings.LLM_MODEL)

    # 3. Web Search Client (optional, used as fallback)
    web_search_client = get_web_search_client()
    
    # 4. LangGraph workflow StateGraph
    compiled_graph = build_rag_graph(_vector_store, _embedding_model, llm_client, web_search_client)
    
    # 5. Services
    _query_service = QueryService(compiled_graph)
    _ingestion_service = IngestionService(_vector_store, _embedding_model)
    _feedback_service = FeedbackService()
    
    logger.info("All services singletons initialized successfully.")

def get_query_service() -> QueryService:
    if _query_service is None:
        raise RuntimeError("QueryService is not initialized.")
    return _query_service

def get_ingestion_service() -> IngestionService:
    if _ingestion_service is None:
        raise RuntimeError("IngestionService is not initialized.")
    return _ingestion_service

def get_feedback_service() -> FeedbackService:
    if _feedback_service is None:
        raise RuntimeError("FeedbackService is not initialized.")
    return _feedback_service
