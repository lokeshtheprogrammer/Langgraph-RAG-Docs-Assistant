import asyncio
import json
import re

from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import GRADING_PROMPT
from app.workflow.state import GradedDoc, RAGState


def parse_grade(response: str) -> str:
    """Parse the relevance grade JSON response from the LLM."""
    cleaned = response.strip()
    if not cleaned:
        return "irrelevant"
        
    try:
        # Strip potential markdown formatting wraps
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
        # Parse JSON
        parsed = json.loads(cleaned)
        grade = parsed.get("grade", "irrelevant").strip().lower()
        if grade in ("relevant", "irrelevant"):
            return grade
        return "irrelevant"
    except Exception as e:
        logger.warning(f"Relevance grade JSON parse failed: {e}. Raw response: {response}")
        return "irrelevant"

def document_grading_node(llm: LLMClientBase):
    """Factory that creates document grading node function."""
    
    async def _grade_single_chunk(question: str, doc, semaphore: asyncio.Semaphore):
        """Grade a single chunk with concurrency control."""
        async with semaphore:
            prompt = GRADING_PROMPT.format(question=question, chunk=doc.content)
            try:
                response = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.0)
                grade = parse_grade(response)
            except Exception as e:
                logger.error(f"Grading request failed for chunk {doc.source_file}#{doc.chunk_index}: {e}")
                grade = "irrelevant"
            return GradedDoc(chunk=doc, grade=grade)
    
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node 3: Document Relevance Grading...")
        question = state["question"]
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not retrieved_docs:
            logger.info("No documents to grade.")
            return {
                "graded_docs": [],
                "relevant_docs": [],
                "should_fallback": state.get("retry_count", 0) >= state.get("max_retries", 2)
            }
        
        # Concurrent grading with semaphore to respect rate limits
        # Use semaphore of 3 to avoid overwhelming the API
        semaphore = asyncio.Semaphore(3)
        tasks = [_grade_single_chunk(question, doc, semaphore) for doc in retrieved_docs]
        graded_docs = await asyncio.gather(*tasks)
        
        relevant_docs = [gd.chunk for gd in graded_docs if gd.grade == "relevant"]
        
        logger.info(f"Grading complete: {len(relevant_docs)} out of {len(retrieved_docs)} chunks relevant.")
        
        # Check if fallback is triggered
        should_fallback = False
        if len(relevant_docs) == 0 and state.get("retry_count", 0) >= state.get("max_retries", 2):
            should_fallback = True
            
        return {
            "graded_docs": list(graded_docs),
            "relevant_docs": relevant_docs,
            "should_fallback": should_fallback
        }
    return node
