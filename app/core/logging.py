import json
import logging
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Merge extra properties if present
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            log_data.update(extra)
            
        return json.dumps(log_data)

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("rag_assistant")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

logger = setup_logger()
