"""Centralized logging configuration for all services.

Provides consistent logging setup across the application with proper
formatting, handlers, and log levels.
"""
import logging as logging_module
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging_module.INFO,
    format_string: Optional[str] = None
) -> logging_module.Logger:
    """Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger = logging_module.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging_module.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Formatter
    formatter = logging_module.Formatter(format_string)
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging_module.Logger:
    """Get or create a logger with default configuration.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        Logger instance
    """
    return setup_logger(name)
