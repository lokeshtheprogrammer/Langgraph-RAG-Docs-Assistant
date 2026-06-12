import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Intercepts HTTP requests, injects unique request_ids, and logs latency durations."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        
        # Log request receipt
        logger.info(
            f"HTTP Request: {request.method} {request.url.path}",
            extra={"extra": {"request_id": request_id, "client_ip": request.client.host if request.client else "unknown"}}
        )
        
        try:
            response = await call_next(request)
            
            # Inject request ID into response headers
            response.headers["X-Request-ID"] = request_id
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"HTTP Response: {request.method} {request.url.path} status={response.status_code} in {duration_ms}ms",
                extra={"extra": {"request_id": request_id, "duration_ms": duration_ms}}
            )
            return response
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                f"HTTP Request Failed: {request.method} {request.url.path} - Error: {e} after {duration_ms}ms",
                extra={"extra": {"request_id": request_id, "duration_ms": duration_ms}},
                exc_info=True
            )
            raise
