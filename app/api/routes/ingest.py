import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.schemas.common import ErrorResponse
from app.api.schemas.ingest import IngestResponse
from app.config import settings
from app.core.exceptions import ValidationError
from app.dependencies import get_ingestion_service
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post(
    "", 
    response_model=IngestResponse, 
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input sources"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def ingest_document(
    file: Annotated[UploadFile | None, File()] = None,
    url: Annotated[str | None, Form()] = None,
    service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> IngestResponse:
    """Ingest a new document from a local file upload or scraping a public URL location."""
    
    # 1. Validation: exact-one check
    if file is None and url is None:
        raise ValidationError("Neither file nor URL source was provided. Exactly one must be specified.")
    if file is not None and url is not None:
        raise ValidationError("Both file and URL sources were provided. Exactly one must be specified.")
        
    # 2. Process URL Ingestion
    if url is not None:
        url_strip = url.strip()
        if not (url_strip.startswith("http://") or url_strip.startswith("https://")):
            raise ValidationError("Invalid URL scheme. URL must start with 'http://' or 'https://'.")
            
        result = await service.ingest_url(url_strip)
        return IngestResponse(**result)
        
    # 3. Process File Ingestion
    if file is not None:
        filename = file.filename
        _, ext = os.path.splitext(filename.lower())
        
        if ext not in settings.ALLOWED_FILE_EXTENSIONS:
            raise ValidationError(
                f"File format '{ext}' is not supported. Allowed formats: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )
            
        # Write to temporary file to process via Loader
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            # Check file size stream
            file_size = 0
            with open(temp_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024) # 1MB chunk reads
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        raise ValidationError(f"File size exceeds the maximum limit of {settings.MAX_FILE_SIZE_MB}MB.")
                    buffer.write(chunk)
            
            if file_size == 0:
                raise ValidationError("Uploaded file is empty.")
                
            # Run ingestion
            result = await service.ingest_file(temp_path)
            return IngestResponse(**result)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
