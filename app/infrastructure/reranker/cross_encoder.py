from sentence_transformers import CrossEncoder

from app.core.logging import logger
from app.workflow.state import DocumentChunk


class CrossEncoderReranker:
    """Reranker using a sentence-transformers Cross-Encoder model to score query-document pairs."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Initializing CrossEncoder reranker model: {model_name}...")
        # CrossEncoder will download the model automatically on first init (~80MB)
        self.model = CrossEncoder(model_name)
        logger.info(f"CrossEncoder reranker model {model_name} initialized successfully.")

    def rerank(self, query: str, docs: list[DocumentChunk]) -> list[DocumentChunk]:
        if not docs:
            return []
        
        logger.info(f"Reranking {len(docs)} document chunks for query: '{query[:100]}'")
        pairs = [[query, doc.content] for doc in docs]
        
        # Predict relevancy scores
        scores = self.model.predict(pairs)
        
        # Sort documents by score in descending order
        sorted_docs_with_scores = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        
        for doc, score in sorted_docs_with_scores:
            logger.info(f"Rerank Score: {score:.4f} for chunk: {doc.source_file} #{doc.chunk_index}")
            
        return [doc for doc, _ in sorted_docs_with_scores]
