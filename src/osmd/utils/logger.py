"""Logging utilities for the OSM Urban Growth Analysis project."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class Logger:
    """Custom logger for the OSM Urban Growth Analysis project."""
    
    def __init__(self, name: str = "osm_urban_growth", level: str = "INFO", 
                 log_file: Optional[str] = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def log_analysis_start(self, bbox: tuple, years: list) -> None:
        """Log the start of an analysis."""
        self.info(f"Starting urban growth analysis for bbox: {bbox}, years: {years}")
    
    def log_data_collection(self, year: int, feature_count: int) -> None:
        """Log data collection progress."""
        self.info(f"Collected {feature_count} features for year {year}")
    
    def log_processing_step(self, step: str, duration: float) -> None:
        """Log processing step completion."""
        self.info(f"Completed {step} in {duration:.2f} seconds")
    
    def log_error_with_context(self, error: Exception, context: str) -> None:
        """Log error with additional context."""
        self.error(f"Error in {context}: {str(error)}")
    
    def log_memory_usage(self, stage: str, memory_mb: float) -> None:
        """Log memory usage at different stages."""
        self.debug(f"Memory usage at {stage}: {memory_mb:.2f} MB")


def get_default_logger(log_to_file: bool = True) -> Logger:
    """
    Get a default logger instance.
    
    Args:
        log_to_file: Whether to log to file
        
    Returns:
        Logger instance
    """
    log_file = None
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/osm_analysis_{timestamp}.log"
    
    return Logger(log_file=log_file)
