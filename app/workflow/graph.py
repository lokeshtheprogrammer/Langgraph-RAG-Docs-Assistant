from langgraph.graph import END, StateGraph

from app.infrastructure.embeddings.base import EmbeddingModelBase
from app.infrastructure.llm.base import LLMClientBase
from app.infrastructure.vector_store.base import VectorStoreBase
from app.infrastructure.web_search.base import WebSearchClientBase
from app.workflow.nodes.document_grading import document_grading_node
from app.workflow.nodes.generation import generation_node
from app.workflow.nodes.hallucination_check import hallucination_check_node
from app.workflow.nodes.query_analysis import query_analysis_node
from app.workflow.nodes.query_rewrite import query_rewrite_node
from app.workflow.nodes.retrieval import retrieval_node
from app.workflow.nodes.web_search import web_search_node
from app.workflow.routing import (
    route_after_analysis,
    route_after_grading,
    route_after_hallucination_check,
)
from app.workflow.state import RAGState


def build_rag_graph(
    vector_store: VectorStoreBase, 
    embedding_model: EmbeddingModelBase, 
    llm_client: LLMClientBase,
    web_search_client: WebSearchClientBase = None,
    reranker = None
):
    """Factory creating the compiled self-corrective RAG LangGraph workflow."""
    
    # 1. Initialize StateGraph with the TypedDict state schema
    workflow = StateGraph(RAGState)
    
    # 2. Add nodes to graph
    workflow.add_node("query_analysis", query_analysis_node(llm_client))
    workflow.add_node("retrieval", retrieval_node(vector_store, embedding_model, reranker=reranker))
    workflow.add_node("document_grading", document_grading_node(llm_client))
    workflow.add_node("generation", generation_node(llm_client))
    workflow.add_node("query_rewrite", query_rewrite_node(llm_client))
    workflow.add_node("hallucination_check", hallucination_check_node(llm_client))
    workflow.add_node("web_search", web_search_node(web_search_client))
    
    # 3. Set entry point node
    workflow.set_entry_point("query_analysis")
    
    # 4. Define conditional/static edges
    workflow.add_conditional_edges(
        "query_analysis",
        route_after_analysis,
        {
            "generate": "generation",
            "retrieve": "retrieval"
        }
    )
    workflow.add_edge("retrieval", "document_grading")

    workflow.add_edge("query_rewrite", "retrieval") # retry loop back
    
    # 5. Define conditional edges routing after grading
    workflow.add_conditional_edges(
        "document_grading",
        route_after_grading,
        {
            "generate": "generation",
            "rewrite": "query_rewrite",
            "web_search": "web_search",
        }
    )

    # Web search routes to generation
    workflow.add_edge("web_search", "generation")
    
    # 6. Direct generation to hallucination check
    workflow.add_edge("generation", "hallucination_check")
    
    # 7. Define conditional edges after hallucination check
    workflow.add_conditional_edges(
        "hallucination_check",
        route_after_hallucination_check,
        {
            "end": END,
            "regenerate": "generation",
        }
    )
    
    # 8. Compile graph
    return workflow.compile()
