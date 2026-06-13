import asyncio
import json
import re

from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import BATCH_GRADING_PROMPT, GRADING_PROMPT
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

def parse_batch_grades(response: str, num_chunks: int) -> dict[int, str]:
    """Parse the relevance grades JSON response from the LLM for batch grading."""
    cleaned = response.strip()
    # Default to irrelevant for all indices
    default_grades = {i: "irrelevant" for i in range(num_chunks)}
    if not cleaned:
        return default_grades
        
    try:
        # Strip potential markdown formatting wraps
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
        # Parse JSON
        parsed = json.loads(cleaned)
        
        # We expect a list of dicts in "grades" or direct list
        grades_list = []
        if isinstance(parsed, dict):
            if "grades" in parsed:
                grades_list = parsed["grades"]
            elif "grade" in parsed:
                # Mock fallback or single grade format: apply to all chunks
                single_grade = parsed.get("grade", "irrelevant").strip().lower()
                if single_grade in ("relevant", "irrelevant"):
                    return {i: single_grade for i in range(num_chunks)}
        elif isinstance(parsed, list):
            grades_list = parsed
            
        grades_map = {}
        for item in grades_list:
            if isinstance(item, dict):
                idx = item.get("chunk_index")
                grade = item.get("grade", "irrelevant").strip().lower()
                if idx is not None and grade in ("relevant", "irrelevant"):
                    grades_map[int(idx)] = grade
                    
        # Merge with defaults to ensure all indices are covered
        for i in range(num_chunks):
            if i not in grades_map:
                grades_map[i] = "irrelevant"
        return grades_map
    except Exception as e:
        logger.warning(f"Batch relevance grade JSON parse failed: {e}. Raw response: {response}")
        return default_grades

def document_grading_node(llm: LLMClientBase):
    """Factory that creates document grading node function."""
    
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node 3: Document Relevance Grading (Batch)...")
        question = state["question"]
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not retrieved_docs:
            logger.info("No documents to grade.")
            return {
                "graded_docs": [],
                "relevant_docs": [],
                "should_fallback": state.get("retry_count", 0) >= state.get("max_retries", 2)
            }
        
        # Format the retrieved documents for batch grading
        chunks_formatted = ""
        for idx, doc in enumerate(retrieved_docs):
            chunks_formatted += f"Chunk {idx}:\n---\n{doc.content}\n---\n\n"
            
        prompt = BATCH_GRADING_PROMPT.format(question=question, chunks_formatted=chunks_formatted)
        
        try:
            response = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.0)
            grades_map = parse_batch_grades(response, len(retrieved_docs))
        except Exception as e:
            logger.error(f"Batch grading request failed: {e}")
            grades_map = {i: "irrelevant" for i in range(len(retrieved_docs))}
            
        graded_docs = []
        for idx, doc in enumerate(retrieved_docs):
            grade = grades_map.get(idx, "irrelevant")
            graded_docs.append(GradedDoc(chunk=doc, grade=grade))
            
        relevant_docs = [gd.chunk for gd in graded_docs if gd.grade == "relevant"]
        
        logger.info(f"Grading complete: {len(relevant_docs)} out of {len(retrieved_docs)} chunks relevant.")
        
        # Check if fallback is triggered
        should_fallback = False
        if len(relevant_docs) == 0 and state.get("retry_count", 0) >= state.get("max_retries", 2):
            should_fallback = True
            
        return {
            "graded_docs": graded_docs,
            "relevant_docs": relevant_docs,
            "should_fallback": should_fallback
        }
    return node

