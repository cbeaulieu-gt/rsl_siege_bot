"""
logger.py
Reusable logging configuration for the siege project.
"""
import logging

# Configure logging for the entire project (only once, on import)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the given name.
    Args:
        name (str): The logger name, usually __name__.
    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
