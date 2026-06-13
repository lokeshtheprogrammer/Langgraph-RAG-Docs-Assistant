from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase
from app.workflow.prompts import (
    CONVERSATIONAL_PROMPT,
    GENERATION_PROMPT,
    REGEN_PROMPT,
    WEB_SEARCH_GENERATION_PROMPT,
)
from app.workflow.state import RAGState, SourceReference

FALLBACK_ANSWER = (
    "I was unable to find relevant information in the documentation corpus to answer your question. "
    "Please check that your question is related to the indexed documents, or consider rephrasing it."
)

def generation_node(llm: LLMClientBase):
    """Factory that creates generation node function."""
    async def node(state: RAGState) -> dict:
        logger.info("Executing Node 4: Generation...")
        
        # Check conversational path
        if state.get("query_type") == "conversational":
            logger.info("Conversational query detected. Generating friendly greeting/response...")
            prompt = CONVERSATIONAL_PROMPT.format(question=state["question"])
            try:
                answer = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.5)
                if not answer or not answer.strip():
                    answer = "Hello! I am your Technical Documentation Copilot. How can I help you today?"
                return {
                    "generation": answer,
                    "sources": [],
                    "should_fallback": False
                }
            except Exception as e:
                logger.error(f"Conversational generation failed: {e}")
                return {
                    "generation": "Hello! I am your Technical Documentation Copilot. How can I help you today?",
                    "sources": [],
                    "should_fallback": False
                }

        # Check fallback path
        if state.get("should_fallback"):
            logger.info("Fallback path active. Skipping generation and returning fallback response.")
            return {
                "generation": FALLBACK_ANSWER,
                "sources": []
            }
            
        relevant_docs = state.get("relevant_docs", [])
        if not relevant_docs:
            logger.info("No relevant documents available for generation. Setting fallback.")
            return {
                "generation": FALLBACK_ANSWER,
                "sources": []
            }

        # Build context from relevant document chunks
        context_parts = []
        sources = []
        
        for doc in relevant_docs:
            context_parts.append(f"[Source: {doc.source_file}, chunk {doc.chunk_index}]\n{doc.content}")
            sources.append(SourceReference(
                source_file=doc.source_file,
                document_id=doc.document_id,
                chunk_index=doc.chunk_index,
                excerpt=doc.content[:300]
            ))
            
        context = "\n\n---\n\n".join(context_parts)
        
        # Track regeneration attempts
        regen_count = state.get("regeneration_count", 0)
        is_regen = state.get("hallucination_check_passed") is False
        if is_regen:
            regen_count += 1
            logger.info(f"Regenerating answer (attempt {regen_count})...")
            
        try:
            query_type = state.get("query_type", "conceptual")
            if is_regen:
                prompt = REGEN_PROMPT.format(
                    context=context,
                    question=state["question"],
                    query_type=query_type,
                    previous_answer=state.get("generation") or ""
                )
                temperature = 0.0 # Strict accuracy for correction
            elif state.get("web_search_used"):
                prompt = WEB_SEARCH_GENERATION_PROMPT.format(
                    context=context,
                    question=state["question"],
                    query_type=query_type
                )
                temperature = 0.3
            else:
                prompt = GENERATION_PROMPT.format(
                    context=context,
                    question=state["question"],
                    query_type=query_type
                )
                temperature = 0.2
                
            answer = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=temperature)
            if not answer or not answer.strip():
                logger.warning("LLM returned an empty answer. Serving fallback.")
                answer = FALLBACK_ANSWER
            logger.info("Generation successful.")
            return {
                "generation": answer,
                "sources": sources,
                "regeneration_count": regen_count
            }
        except Exception as e:
            logger.error(f"Generation request failed: {e}")
            # Safe recovery
            return {
                "generation": "An error occurred while generating the answer. Please try again.",
                "sources": [],
                "regeneration_count": regen_count
            }
    return node

