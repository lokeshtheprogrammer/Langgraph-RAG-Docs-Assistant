from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, feedback, health, ingest, metrics, query
from app.core.database import initialize_db
from app.core.exceptions import (
    DatabaseError,
    LLMProviderError,
    RAGError,
    ValidationError,
    VectorStoreError,
)
from app.core.logging import logger
from app.core.middleware import RequestCorrelationMiddleware
from app.dependencies import initialize_services

app = FastAPI(
    title="RAG Technical Documentation Assistant",
    description="Self-corrective RAG system powered by LangGraph, Groq, and Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Custom Middlewares
app.add_middleware(RequestCorrelationMiddleware)

# Event Hooks
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API Application...")
    # Initialize SQLite database
    initialize_db()
    # Initialize Service Singletons (embeddings, ChromaDB, Graph engine)
    initialize_services()
    logger.info("Application startup sequence completed successfully.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API Application...")

# Global Exception Handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"Request validation failure: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details
            },
            "request_id": request_id
        }
    )

@app.exception_handler(RAGError)
async def rag_exception_handler(request: Request, exc: RAGError):
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Map subtypes to appropriate HTTP codes
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
    
    if isinstance(exc, LLMProviderError):
        error_code = "LLM_PROVIDER_ERROR"
    elif isinstance(exc, VectorStoreError):
        error_code = "VECTOR_STORE_ERROR"
    elif isinstance(exc, DatabaseError):
        error_code = "DATABASE_ERROR"
        
    logger.error(f"RAG system exception ({error_code}): {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.message,
                "details": exc.details
            },
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.critical(f"Unhandled system exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Reference the request ID for support.",
                "details": {}
            },
            "request_id": request_id
        }
    )

# Include endpoint routes
app.include_router(health.router)
app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(feedback.router)
app.include_router(metrics.router)
