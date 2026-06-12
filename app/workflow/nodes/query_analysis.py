import json
import re

from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import QUERY_ANALYSIS_PROMPT
from app.workflow.state import RAGState


def query_analysis_node(llm: LLMClientBase):
    """Factory that creates query analysis node function."""
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node 1: Query Analysis...")
        prompt = QUERY_ANALYSIS_PROMPT.format(question=state["question"])
        
        try:
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            
            # Clean possible markdown JSON formatting wrappers
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # strip out markdown blocks
                cleaned_response = re.sub(r"^```(?:json)?\n", "", cleaned_response)
                cleaned_response = re.sub(r"\n```$", "", cleaned_response)
                cleaned_response = cleaned_response.strip()
                
            parsed = json.loads(cleaned_response)
            rewritten = parsed.get("rewritten_query", state["question"])
            query_type = parsed.get("query_type", "conceptual")
        except Exception as e:
            logger.warning(f"Failed to parse query analysis output: {e}. Falling back to original question.")
            rewritten = state["question"]
            query_type = "conceptual"
            
        logger.info(f"Query Analysis complete: rewritten='{rewritten}', type='{query_type}'")
        return {
            "rewritten_query": rewritten,
            "query_type": query_type
        }
    return node
