from app.core.logging import logger
from app.workflow.state import RAGState


def route_after_grading(state: RAGState) -> str:
    """Determine the next node to transition to based on relevance grading and retries count.

    Returns:
        "generate": proceed to generate answer with relevant context.
        "rewrite": all retrieved docs irrelevant; rewrite query and re-retrieve.
        "fallback": max retries reached; route to generation to render fallback.
    """
    has_relevant = len(state.get("relevant_docs", [])) > 0
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if has_relevant:
        logger.info("Routing after grading: relevant documents found -> 'generate'")
        return "generate"
    elif retry_count < max_retries:
        logger.info(f"Routing after grading: no relevant documents, retry {retry_count}/{max_retries} -> 'rewrite'")
        return "rewrite"
    else:
        logger.info(f"Routing after grading: no relevant documents and max retries ({max_retries}) reached -> 'web_search'")
        return "web_search"

def route_after_hallucination_check(state: RAGState) -> str:
    """Determine routing after grounding checks.
    
    Returns:
        "end": grounding check passed or max regeneration limit reached.
        "regenerate": grounding check failed; loop back to generate node.
    """
    passed = state.get("hallucination_check_passed", True)
    regen_count = state.get("regeneration_count", 0)
    
    if passed:
        logger.info("Routing after hallucination check: answer grounded -> 'end'")
        return "end"
    elif regen_count < 1:
        logger.info(f"Routing after hallucination check: ungrounded, retry {regen_count + 1}/1 -> 'regenerate'")
        return "regenerate"
    else:
        logger.warning("Routing after hallucination check: ungrounded, but max regeneration limit reached -> 'end'")
        return "end"

def route_after_analysis(state: RAGState) -> str:
    """Determine routing after query analysis.
    
    If the query is casual/conversational (greeting/chit-chat), route directly
    to generation to reply without vector store search. Otherwise, retrieve.
    """
    q_type = state.get("query_type")
    if q_type == "conversational":
        logger.info("Routing after query analysis: conversational query -> 'generate'")
        return "generate"
    
    logger.info(f"Routing after query analysis: query type is {q_type} -> 'retrieve'")
    return "retrieve"

