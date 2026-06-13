from typing import Literal, TypedDict

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    content: str
    source_file: str
    document_id: str
    chunk_index: int
    distance: float | None = None

class SourceReference(BaseModel):
    source_file: str
    document_id: str
    chunk_index: int
    excerpt: str

class GradedDoc(BaseModel):
    chunk: DocumentChunk
    grade: Literal["relevant", "irrelevant"]

class RAGState(TypedDict):
    # Input
    question: str
    session_id: str | None

    # Query Analysis
    rewritten_query: str
    query_type: str | None

    # Retrieval
    retrieved_docs: list[DocumentChunk]
    top_k: int
    filter_filenames: list[str] | None  # scope search to specific document(s)

    # Grading
    graded_docs: list[GradedDoc]
    relevant_docs: list[DocumentChunk]

    # Retry Logic
    retry_count: int
    max_retries: int
    should_fallback: bool

    # Generation
    generation: str | None
    sources: list[SourceReference]
    llm_provider_status: str | None

    # Web Search Fallback
    web_search_results: list
    web_search_used: bool

    # Optional/Enhancements
    hallucination_score: float | None
    hallucination_check_passed: bool | None
    regeneration_count: int
