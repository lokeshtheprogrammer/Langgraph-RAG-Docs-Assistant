from app.core.logging import logger
from app.infrastructure.embeddings.base import EmbeddingModelBase
from app.infrastructure.vector_store.base import VectorStoreBase
from app.workflow.state import RAGState


def retrieval_node(vector_store: VectorStoreBase, embedding_model: EmbeddingModelBase, reranker=None):
    """Factory that creates retrieval node function."""
    async def node(state: RAGState) -> dict:
        query = state.get("rewritten_query") or state["question"]
        k = state.get("top_k") or 5
        filter_filenames = state.get("filter_filenames")  # optional document scope
        logger.info(f"Executing Node 2: Retrieval for query='{query[:100]}' (k={k})...")
        if filter_filenames:
            logger.info(f"Retrieval scoped to files: {filter_filenames}")

        try:
            # 1. Embed query
            query_vector = embedding_model.embed_query(query)

            # 2. Build optional ChromaDB metadata filter
            where_filter: dict | None = None
            if filter_filenames:
                if len(filter_filenames) == 1:
                    where_filter = {"source_file": {"$eq": filter_filenames[0]}}
                else:
                    where_filter = {"source_file": {"$in": filter_filenames}}

            # 3. Search (using hybrid search if supported, fallback to vector search)
            # Retrieve more candidate documents if reranking is enabled to give it enough pool to rerank
            retrieve_k = k * 3 if reranker else k
            if hasattr(vector_store, "hybrid_search"):
                docs = vector_store.hybrid_search(
                    query, query_vector, k=retrieve_k, where_filter=where_filter
                )
            else:
                docs = vector_store.similarity_search_by_vector(
                    query_vector, k=retrieve_k, where_filter=where_filter
                )
            logger.info(f"Retrieved {len(docs)} document chunks (pre-rerank).")

            # 4. Apply Cross-Encoder Reranking if available
            if reranker and docs:
                docs = reranker.rerank(query, docs)
                # Keep top k after reranking
                docs = docs[:k]
                logger.info(f"Reranked document chunks. Kept top {len(docs)} chunks.")

            return {"retrieved_docs": docs}
        except Exception as e:
            logger.error(f"Retrieval node execution failed: {e}")
            return {"retrieved_docs": []}
    return node
