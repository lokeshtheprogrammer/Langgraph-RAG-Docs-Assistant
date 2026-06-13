from app.core.exceptions import LLMProviderError
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
        from app.config import settings
        from app.infrastructure.llm.adapters import active_provider_var
        
        # Check conversational path
        if state.get("query_type") == "conversational":
            logger.info("Conversational query detected. Generating friendly greeting/response...")
            prompt = CONVERSATIONAL_PROMPT.format(question=state["question"])
            try:
                answer = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.5)
                if not answer or not answer.strip():
                    answer = "Hello! I am your Technical Documentation Copilot. How can I help you today?"
                provider_status = active_provider_var.get()
                if not provider_status:
                    provider_status = "primary_gemini" if settings.LLM_PROVIDER == "google" else "primary_groq"
                return {
                    "generation": answer,
                    "sources": [],
                    "should_fallback": False,
                    "llm_provider_status": provider_status
                }
            except Exception as e:
                logger.error(f"Conversational generation failed: {e}")
                return {
                    "generation": "Hello! I am your Technical Documentation Copilot. How can I help you today?",
                    "sources": [],
                    "should_fallback": False,
                    "llm_provider_status": "retrieval_only"
                }

        # Check fallback path
        if state.get("should_fallback"):
            logger.info("Fallback path active. Skipping generation and returning fallback response.")
            provider_status = active_provider_var.get()
            if not provider_status:
                provider_status = "primary_gemini" if settings.LLM_PROVIDER == "google" else "primary_groq"
            return {
                "generation": FALLBACK_ANSWER,
                "sources": [],
                "llm_provider_status": provider_status
            }
            
        relevant_docs = state.get("relevant_docs", [])
        if not relevant_docs:
            logger.info("No relevant documents available for generation. Setting fallback.")
            provider_status = active_provider_var.get()
            if not provider_status:
                provider_status = "primary_gemini" if settings.LLM_PROVIDER == "google" else "primary_groq"
            return {
                "generation": FALLBACK_ANSWER,
                "sources": [],
                "llm_provider_status": provider_status
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
            
            provider_status = active_provider_var.get()
            if not provider_status:
                provider_status = "primary_gemini" if settings.LLM_PROVIDER == "google" else "primary_groq"
                
            return {
                "generation": answer,
                "sources": sources,
                "regeneration_count": regen_count,
                "llm_provider_status": provider_status
            }
        except LLMProviderError as e:
            logger.error(f"Generation request failed due to LLM provider error: {e}")
            active_provider_var.set("retrieval_only")
            
            # Retrieval-Only Fallback
            docs_to_use = relevant_docs or state.get("retrieved_docs", [])
            
            # Format fallback message exactly matching requirements
            fallback_generation = (
                "AI generation is temporarily unavailable because all configured "
                "AI providers have reached their limits.\n\n"
                "Most relevant information found:\n"
            )
            
            # Format each source snippet
            sources_list = []
            for doc in docs_to_use[:3]:  # Top relevant chunks
                fallback_generation += f"\n[Source: {doc.source_file}]\n{doc.content}\n"
                sources_list.append(SourceReference(
                    source_file=doc.source_file,
                    document_id=doc.document_id,
                    chunk_index=doc.chunk_index,
                    excerpt=doc.content[:300]
                ))
                
            if len(docs_to_use) > 3:
                fallback_generation += "\nAdditional relevant passages:\n"
                for doc in docs_to_use[3:6]:
                    fallback_generation += f"- [Source: {doc.source_file}] {doc.content[:150]}...\n"
                    
            return {
                "generation": fallback_generation,
                "sources": sources_list,
                "should_fallback": True,  # Skip grounding/hallucination check
                "llm_provider_status": "retrieval_only",
                "regeneration_count": regen_count
            }
        except Exception as e:
            # Re-raise other exceptions (e.g. database/parsing/code bugs) as real errors
            logger.critical(f"Generation request encountered unhandled error: {e}")
            raise e
    return node

