from app.core.logging import logger
from app.infrastructure.embeddings.base import EmbeddingModelBase
from app.infrastructure.vector_store.base import VectorStoreBase
from app.workflow.state import RAGState


def retrieval_node(vector_store: VectorStoreBase, embedding_model: EmbeddingModelBase):
    """Factory that creates retrieval node function."""
    async def node(state: RAGState) -> dict:
        query = state.get("rewritten_query") or state["question"]
        k = state.get("top_k") or 5
        logger.info(f"Executing Node 2: Retrieval for query='{query[:100]}' (k={k})...")
        
        try:
            # 1. Embed query
            query_vector = embedding_model.embed_query(query)
            
            # 2. Similarity search
            docs = vector_store.similarity_search_by_vector(query_vector, k=k)
            logger.info(f"Retrieved {len(docs)} document chunks.")
            return {"retrieved_docs": docs}
        except Exception as e:
            logger.error(f"Retrieval node execution failed: {e}")
            return {"retrieved_docs": []}
    return node
