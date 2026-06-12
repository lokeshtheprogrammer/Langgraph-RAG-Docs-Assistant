from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import REWRITE_PROMPT
from app.workflow.state import RAGState


def query_rewrite_node(llm: LLMClientBase):
    """Factory that creates query rewrite node function."""
    async def node(state: RAGState) -> dict:
        current_retry = state.get("retry_count", 0)
        logger.info(f"Executing Node: Query Rewrite (attempt {current_retry + 1})...")
        
        prompt = REWRITE_PROMPT.format(
            question=state["question"],
            rewritten_query=state.get("rewritten_query", state["question"]),
            retry_count=current_retry + 1
        )
        
        try:
            new_query = await llm.ainvoke([{"role": "user", "content": prompt}])
            rewritten = new_query.strip().strip('"').strip("'")
            if not rewritten:
                rewritten = state["question"]
        except Exception as e:
            logger.warning(f"Failed to invoke query rewrite LLM: {e}. Reverting to original query.")
            rewritten = state["question"]
            
        logger.info(f"Query rewritten: '{rewritten}'")
        return {
            "rewritten_query": rewritten,
            "retry_count": current_retry + 1
        }
    return node
