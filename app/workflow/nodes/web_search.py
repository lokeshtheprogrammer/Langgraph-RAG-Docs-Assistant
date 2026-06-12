import uuid

from app.core.logging import logger
from app.infrastructure.web_search.base import WebSearchClientBase
from app.workflow.state import DocumentChunk, RAGState


def web_search_node(web_search_client: WebSearchClientBase):
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node: Web Search Fallback...")

        if web_search_client is None:
            logger.warning("Web search client is not available. Skipping web search.")
            return {
                "web_search_results": [],
                "web_search_used": False,
                "should_fallback": True
            }

        query = state.get("rewritten_query") or state["question"]
        logger.info(f"Searching web for: '{query[:100]}'")

        try:
            results = await web_search_client.search(query, num_results=5)

            if not results:
                logger.info("Web search returned no results.")
                return {
                    "web_search_results": [],
                    "web_search_used": True,
                    "should_fallback": True
                }

            # Convert web results to DocumentChunks for the generation node
            doc_id = f"web_{uuid.uuid4().hex[:8]}"
            chunks = []
            for i, r in enumerate(results):
                content = f"Title: {r.title}\nURL: {r.url}\nContent: {r.snippet}"
                if r.content and len(r.content) > len(r.snippet):
                    content = f"Title: {r.title}\nURL: {r.url}\nContent: {r.content}"

                chunks.append(DocumentChunk(
                    content=content,
                    source_file=f"[Web] {r.title}",
                    document_id=doc_id,
                    chunk_index=i
                ))

            logger.info(f"Web search returned {len(chunks)} results. Converting to document chunks.")
            return {
                "web_search_results": [r.model_dump() for r in results],
                "web_search_used": True,
                "should_fallback": False,
                "retrieved_docs": chunks,
                "relevant_docs": chunks
            }

        except Exception as e:
            logger.error(f"Web search node execution failed: {e}")
            return {
                "web_search_results": [],
                "web_search_used": True,
                "should_fallback": True
            }
    return node
