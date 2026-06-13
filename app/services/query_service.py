import time

from app.api.schemas.query import DebugChunk, QueryRequest, QueryResponse, SourceReference
from app.core.database import get_db_connection
from app.core.logging import logger
from app.repositories.chat_history import ChatHistoryRepository
from app.repositories.query_log_repository import QueryLogRepository


class QueryService:
    """Invokes compiled StateGraph with conversation memory and maps output to QueryResponse."""

    def __init__(self, compiled_graph):
        self.graph = compiled_graph

    @staticmethod
    def _compute_confidence(result: dict) -> float:
        """Compute a composite confidence score (0.0-1.0) from LangGraph result state.

        Weighted formula:
          - Grounding score (40%): hallucination_score from the grounding verifier
          - Retrieval quality (40%): ratio of relevant docs to total retrieved
          - Retry penalty (20%): penalized by retry count and fallback usage
        """
        # 1. Grounding component (weight: 0.4)
        grounding = result.get("hallucination_score")
        grounding_score = grounding if grounding is not None else 0.5  # neutral default

        # 2. Retrieval quality component (weight: 0.4)
        retrieved = result.get("retrieved_docs", [])
        relevant = result.get("relevant_docs", [])
        if retrieved:
            retrieval_score = len(relevant) / len(retrieved)
        else:
            retrieval_score = 0.0

        # 3. Retry/fallback penalty component (weight: 0.2)
        retry_count = result.get("retry_count", 0)
        max_retries = result.get("max_retries", 2)
        is_fallback = result.get("should_fallback", False)
        if is_fallback:
            retry_score = 0.1  # heavy penalty for fallback
        elif max_retries > 0:
            retry_score = max(0.0, 1.0 - (retry_count / max_retries))
        else:
            retry_score = 1.0

        # Weighted combination
        confidence = (0.4 * grounding_score) + (0.4 * retrieval_score) + (0.2 * retry_score)
        return round(min(1.0, max(0.0, confidence)), 3)

    def _load_chat_context(self, session_id: str | None) -> str:
        """Load recent conversation history for the session and format as context prefix."""
        if not session_id:
            return ""
        try:
            with get_db_connection() as conn:
                history = ChatHistoryRepository.get_history(conn, session_id, limit=6)
            if not history:
                return ""
            
            lines = []
            for turn in history:
                role = "User" if turn["role"] == "user" else "Assistant"
                lines.append(f"{role}: {turn['content']}")
            
            context = "\n".join(lines)
            logger.info(f"Loaded {len(history)} conversation turns for session {session_id}")
            return context
        except Exception as e:
            logger.warning(f"Failed to load chat history: {e}")
            return ""

    def _save_turn(self, session_id: str | None, role: str, content: str):
        """Persist a conversation turn to the database."""
        if not session_id:
            return
        try:
            with get_db_connection() as conn:
                ChatHistoryRepository.insert_turn(conn, session_id, role, content)
        except Exception as e:
            logger.warning(f"Failed to save chat turn: {e}")

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        logger.info(f"Processing query: '{request.question[:100]}'")
        start_time = time.perf_counter()

        # Load conversation memory
        chat_context = self._load_chat_context(request.session_id)
        
        # Enhance question with conversation context for follow-up queries
        effective_question = request.question
        if chat_context:
            effective_question = (
                f"Conversation history:\n{chat_context}\n\n"
                f"Current question: {request.question}"
            )
            logger.info("Augmented question with conversation history context.")

        # Initialize State
        initial_state = {
            "question": effective_question,
            "session_id": request.session_id,
            "top_k": request.top_k or 5,
            "retry_count": 0,
            "max_retries": request.max_retries or 2,
            "should_fallback": False,
            "retrieved_docs": [],
            "graded_docs": [],
            "relevant_docs": [],
            "web_search_results": [],
            "web_search_used": False
        }

        # Invoke LangGraph StateGraph
        result = await self.graph.ainvoke(initial_state)
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"Query processing completed in {duration_ms}ms")

        # Persist conversation turns
        self._save_turn(request.session_id, "user", request.question)
        answer_text = result.get("generation", "No response generated.")
        self._save_turn(request.session_id, "assistant", answer_text)

        # Map sources to validation schemas
        sources = [
            SourceReference(
                source_file=src.source_file,
                document_id=src.document_id,
                chunk_index=src.chunk_index,
                excerpt=src.excerpt
            )
            for src in result.get("sources", [])
        ]

        # Build debug trace - retrieved chunks
        retrieved_chunks = None
        raw_retrieved = result.get("retrieved_docs", [])
        if raw_retrieved:
            retrieved_chunks = [
                DebugChunk(
                    content=doc.content[:500],
                    source_file=doc.source_file,
                    chunk_index=doc.chunk_index,
                    grade=None,
                    distance=doc.distance
                )
                for doc in raw_retrieved
            ]

        # Build debug trace - graded chunks with relevance labels
        graded_chunks = None
        raw_graded = result.get("graded_docs", [])
        if raw_graded:
            graded_chunks = [
                DebugChunk(
                    content=gd.chunk.content[:500],
                    source_file=gd.chunk.source_file,
                    chunk_index=gd.chunk.chunk_index,
                    grade=gd.grade,
                    distance=gd.chunk.distance
                )
                for gd in raw_graded
            ]

        # Compute composite confidence score
        confidence = self._compute_confidence(result)
        logger.info(f"Confidence score: {confidence}")

        # Log query execution for analytics (fire-and-forget)
        try:
            with get_db_connection() as conn:
                QueryLogRepository.insert_log(conn, {
                    "question": request.question[:500],
                    "query_type": result.get("query_type"),
                    "rewritten_query": result.get("rewritten_query", "")[:500],
                    "retry_count": result.get("retry_count", 0),
                    "is_fallback": 1 if result.get("should_fallback") else 0,
                    "web_search_used": 1 if result.get("web_search_used") else 0,
                    "hallucination_score": result.get("hallucination_score"),
                    "confidence_score": confidence,
                    "response_time_ms": duration_ms,
                    "source_count": len(sources),
                    "session_id": request.session_id,
                })
        except Exception as e:
            logger.warning(f"Failed to log query execution: {e}")

        return QueryResponse(
            answer=answer_text,
            sources=sources,
            query_type=result.get("query_type", "conceptual"),
            rewritten_query=result.get("rewritten_query", request.question),
            retry_count=result.get("retry_count", 0),
            is_fallback=result.get("should_fallback", False),
            response_time_ms=duration_ms,
            session_id=request.session_id,
            retrieved_chunks=retrieved_chunks,
            graded_chunks=graded_chunks,
            hallucination_score=result.get("hallucination_score"),
            confidence_score=confidence,
            retrieval_count=len(raw_retrieved),
            relevant_chunk_count=len(result.get("relevant_docs", []))
        )
