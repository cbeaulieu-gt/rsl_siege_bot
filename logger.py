"""
logger.py
Reusable logging configuration for the siege project.
"""
import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add color to log messages."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[37m',      # White
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    RESET = '\033[0m'  # Reset to default color
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with appropriate color for the level.
        
        Args:
            record (logging.LogRecord): The log record to format.
            
        Returns:
            str: Formatted log message with color codes.
        """
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


# Global flag to track initialization
_logging_configured: bool = False


def _configure_logging() -> None:
    """Configure logging with colored output for the entire project."""
    global _logging_configured
    
    # Only configure if not already done
    if _logging_configured:
        return
        
    # Create colored formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Mark as configured
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the given name.
    
    Args:
        name (str): The logger name, usually __name__.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure logging is configured before returning logger
    _configure_logging()
    return logging.getLogger(name)


# Configure logging once when module is imported
_configure_logging()
