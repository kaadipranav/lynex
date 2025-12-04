"""
Structured Logging Module.
Provides JSON logging configuration for production environments.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def __init__(self, service_name: str, environment: str):
        self.service_name = service_name
        self.environment = environment
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        return json.dumps(log_record)

def configure_logging(
    service_name: str,
    environment: str,
    log_level: str = "INFO",
    json_format: bool = False
):
    """
    Configure logging for the service.
    
    Args:
        service_name: Name of the service (e.g., "ingest-api")
        environment: Current environment (development, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Whether to output logs in JSON format (recommended for prod)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format or environment.lower() == "production":
        formatter = JSONFormatter(service_name, environment)
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set levels for third-party libraries to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured for {service_name} in {environment} mode")
