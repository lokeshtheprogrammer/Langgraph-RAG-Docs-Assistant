import time

from app.api.schemas.query import DebugChunk, QueryRequest, QueryResponse, SourceReference
from app.core.database import get_db_connection
from app.core.logging import logger
from app.repositories.chat_history import ChatHistoryRepository


class QueryService:
    """Invokes compiled StateGraph with conversation memory and maps output to QueryResponse."""

    def __init__(self, compiled_graph):
        self.graph = compiled_graph

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
                    grade=None
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
                    grade=gd.grade
                )
                for gd in raw_graded
            ]

        return QueryResponse(
            answer=answer_text,
            sources=sources,
            query_type=result.get("query_type", "conceptual"),
            rewritten_query=result.get("rewritten_query", request.question),
            retry_count=result.get("retry_count", 0),
            is_fallback=result.get("should_fallback", False),
            response_time_ms=duration_ms,
            session_id=request.session_id,
            # Debug trace fields
            retrieved_chunks=retrieved_chunks,
            graded_chunks=graded_chunks,
            hallucination_score=result.get("hallucination_score")
        )
