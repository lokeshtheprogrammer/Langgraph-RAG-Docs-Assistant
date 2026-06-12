from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.schemas.common import ErrorResponse
from app.api.schemas.query import QueryRequest, QueryResponse
from app.dependencies import get_query_service
from app.services.query_service import QueryService

router = APIRouter(prefix="/query", tags=["Query"])

@router.post(
    "", 
    response_model=QueryResponse, 
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "LLM or DB service unavailable"}
    }
)
async def query_assistant(
    request: QueryRequest,
    service: Annotated[QueryService, Depends(get_query_service)]
) -> QueryResponse:
    """Submit a natural language question and receive a grounded answer with citations."""
    try:
        response = await service.process_query(request)
        return response
    except Exception:
        # FastAPI global exception handler middleware catches RAGExceptions
        raise
