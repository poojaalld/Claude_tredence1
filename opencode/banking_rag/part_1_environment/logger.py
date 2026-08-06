"""
Logger configuration for Banking RAG Assistant
"""

import sys
from pathlib import Path
from loguru import logger

try:
    from .config import settings
except ImportError:
    from config import settings


def setup_logger():
    """Configure logger for the application"""
    
    # Remove default handler
    logger.remove()
    
    # Create logs directory
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Log format
    log_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler
    log_file = logs_dir / "app.log"
    logger.add(
        str(log_file),
        format=log_format,
        level=settings.log_level,
        rotation="500 MB",
        retention="7 days",
        compression="zip",
    )
    
    # Error file handler
    error_log_file = logs_dir / "error.log"
    logger.add(
        str(error_log_file),
        format=log_format,
        level="ERROR",
        rotation="500 MB",
        retention="7 days",
        compression="zip",
    )
    
    return logger


# Initialize logger
log = setup_logger()
