import re
from rank_bm25 import BM25Okapi

from app.core.logging import logger
from app.infrastructure.vector_store.base import VectorStoreBase
from app.workflow.state import DocumentChunk


class HybridVectorStore(VectorStoreBase):
    """Hybrid vector store wrapping ChromaVectorStore with BM25 keyword search and RRF merging."""

    def __init__(self, chroma_store: VectorStoreBase):
        self.chroma_store = chroma_store
        # Cache of where_filter string -> (bm25_instance, chunks_list)
        self._cache = {}

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        self.clear_cache()
        return self.chroma_store.add_chunks(chunks, embeddings)

    def delete_by_document_id(self, document_id: str) -> None:
        self.clear_cache()
        return self.chroma_store.delete_by_document_id(document_id)

    def get_all_chunks(self, where_filter: dict | None = None) -> list[DocumentChunk]:
        return self.chroma_store.get_all_chunks(where_filter)

    def clear_cache(self) -> None:
        logger.info("Clearing HybridVectorStore BM25 cache.")
        self._cache.clear()

    def similarity_search_by_vector(
        self, vector: list[float], k: int = 5, where_filter: dict | None = None
    ) -> list[DocumentChunk]:
        return self.chroma_store.similarity_search_by_vector(vector, k, where_filter)

    def hybrid_search(
        self, query: str, query_vector: list[float], k: int = 5, where_filter: dict | None = None
    ) -> list[DocumentChunk]:
        logger.info(f"Performing hybrid search for query: '{query}'")

        # 1. Fetch all candidate chunks for BM25
        cache_key = str(where_filter)
        if cache_key in self._cache:
            bm25, corpus_chunks = self._cache[cache_key]
        else:
            corpus_chunks = self.get_all_chunks(where_filter)
            if corpus_chunks:
                # Tokenize corpus
                tokenized_corpus = [self._tokenize(chunk.content) for chunk in corpus_chunks]
                bm25 = BM25Okapi(tokenized_corpus)
                self._cache[cache_key] = (bm25, corpus_chunks)
            else:
                bm25 = None
                corpus_chunks = []

        # 2. Run BM25 search
        bm25_results = []
        if bm25 and corpus_chunks:
            tokenized_query = self._tokenize(query)
            scores = bm25.get_scores(tokenized_query)
            # Pair chunks with scores and sort
            chunk_scores = list(zip(corpus_chunks, scores))
            # Sort descending by score, only keep those with score > 0
            sorted_bm25 = sorted([cs for cs in chunk_scores if cs[1] > 0], key=lambda x: x[1], reverse=True)
            bm25_results = [chunk for chunk, score in sorted_bm25]

        # 3. Run Vector search (retrieve more than k to get good candidates for merging)
        vector_results = self.similarity_search_by_vector(query_vector, k=max(k * 2, 20), where_filter=where_filter)

        # 4. Merge results using Reciprocal Rank Fusion (RRF)
        rrf_scores = {}

        def add_rrf_scores(results_list):
            for rank, chunk in enumerate(results_list):
                key = (chunk.source_file, chunk.chunk_index)
                if key not in rrf_scores:
                    rrf_scores[key] = {"chunk": chunk, "score": 0.0}
                # 1-based rank
                rrf_scores[key]["score"] += 1.0 / (60.0 + (rank + 1))

        add_rrf_scores(vector_results)
        add_rrf_scores(bm25_results)

        # Sort chunks by RRF score descending
        sorted_chunks = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
        merged_chunks = [item["chunk"] for item in sorted_chunks]

        logger.info(f"Hybrid search merged {len(vector_results)} vector and {len(bm25_results)} BM25 results into {len(merged_chunks)} sorted chunks.")

        # Return top k
        return merged_chunks[:k]

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())
