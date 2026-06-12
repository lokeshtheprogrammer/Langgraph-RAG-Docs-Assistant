import json
import re

from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import HALLUCINATION_PROMPT
from app.workflow.state import RAGState


def parse_hallucination_check(response: str) -> tuple[float, bool]:
    """Parse JSON output from the hallucination check LLM.
    
    Returns:
        tuple (score, supported_bool)
    """
    cleaned = response.strip()
    if not cleaned:
        return 0.0, False
        
    try:
        # Strip potential markdown formatting wrappers
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
        parsed = json.loads(cleaned)
        score = float(parsed.get("score", 0.0))
        supported = bool(parsed.get("supported", score >= 0.7))
        return score, supported
    except Exception as e:
        logger.warning(f"Hallucination check JSON parse failed: {e}. Raw response: {response}")
        # Default to safe fail state
        return 0.0, False

def hallucination_check_node(llm: LLMClientBase):
    """Factory that creates the hallucination verification node function."""
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node: Hallucination Check...")
        
        # If fallback response or conversational response, skip hallucination check
        if state.get("should_fallback") or state.get("query_type") == "conversational":
            logger.info("Fallback or conversational query active. Skipping hallucination check.")
            return {
                "hallucination_score": 1.0,
                "hallucination_check_passed": True
            }

            
        relevant_docs = state.get("relevant_docs", [])
        generation = state.get("generation")
        
        if not relevant_docs or not generation:
            logger.warning("Missing context or generation for hallucination check.")
            return {
                "hallucination_score": 0.0,
                "hallucination_check_passed": False
            }

        # Build context representation
        context = "\n\n".join(doc.content for doc in relevant_docs)
        prompt = HALLUCINATION_PROMPT.format(context=context, answer=generation)
        
        try:
            # low temperature for factual checker
            response = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.0)
            score, passed = parse_hallucination_check(response)
        except Exception as e:
            logger.error(f"Hallucination check request failed: {e}")
            score, passed = 0.0, False
            
        logger.info(f"Hallucination check complete: score={score:.2f}, passed={passed}")
        return {
            "hallucination_score": score,
            "hallucination_check_passed": passed
        }
    return node
