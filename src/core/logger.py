"""
Logging infrastructure for ClusterM
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .config import Config


class Logger:
    """Centralized logger for ClusterM"""
    
    _instance: Optional['Logger'] = None
    
    def __new__(cls, config: Optional[Config] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Config] = None):
        if self._initialized:
            return
        
        self.config = config
        self.logger = logging.getLogger("clusterm")
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration"""
        level = logging.INFO
        if self.config:
            level_str = self.config.get('app.log_level', 'INFO')
            level = getattr(logging, level_str.upper(), logging.INFO)
        
        self.logger.setLevel(level)
        
        # File handler only - no console output to prevent Textual UI interference
        log_dir = Path.home() / ".clusterm" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "clusterm.log")
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Clear existing handlers and add file handler only
        self.logger.handlers.clear()
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)