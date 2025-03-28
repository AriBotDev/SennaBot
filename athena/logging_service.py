"""
Enhanced logging service for SennaBot.
Handles different log types, rotation, and streaming to console.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime

class LoggingService:
    """
    Comprehensive logging service with different log levels, 
    file rotation, and specialized loggers for different types of events.
    """
    
    # Main loggers
    main_logger = None
    command_logger = None
    error_logger = None
    debug_logger = None
    
    # Constants
    LOGS_DIR = "logs"
    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
    BACKUP_COUNT = 5                # Keep 5 rotated files
    
    @classmethod
    def initialize(cls):
        """Initialize the logging service."""
        # Ensure logs directory exists
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        
        # Set up the main bot logger
        cls.main_logger = cls._create_logger(
            "bot_main",
            os.path.join(cls.LOGS_DIR, "bot_main.log"),
            logging.INFO
        )
        
        # Set up command event logger
        cls.command_logger = cls._create_logger(
            "command_events",
            os.path.join(cls.LOGS_DIR, "command_events.log"),
            logging.INFO
        )
        
        # Set up error logger
        cls.error_logger = cls._create_logger(
            "error_reports", 
            os.path.join(cls.LOGS_DIR, "error_reports.log"),
            logging.ERROR
        )
        
        # Set up debug logger (this one doesn't send to console by default)
        cls.debug_logger = cls._create_logger(
            "debug", 
            os.path.join(cls.LOGS_DIR, "debug.log"),
            logging.DEBUG,
            False  # Don't send debug logs to console
        )
        
        # Log initialization
        cls.main_logger.info("Logging service initialized")
    
    @classmethod
    def _create_logger(cls, name, log_file, level, console_output=True):
        """Create a logger with file and optional console handlers."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove any existing handlers to prevent duplicates on reload
        if logger.handlers:
            logger.handlers.clear()
        
        # Create file handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=cls.MAX_LOG_SIZE,
            backupCount=cls.BACKUP_COUNT
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    @classmethod
    def get_logger(cls, name):
        """Get an existing logger by name or create a new specialized one."""
        if name == "main":
            return cls.main_logger
        elif name == "command":
            return cls.command_logger
        elif name == "error":
            return cls.error_logger
        elif name == "debug":
            return cls.debug_logger
        else:
            # Create specialized logger
            return cls._create_logger(
                name,
                os.path.join(cls.LOGS_DIR, f"{name}.log"),
                logging.INFO
            )
    
    @classmethod
    def log(cls, message, level="info", logger="main"):
        """Log a message with the specified level to the specified logger."""
        log = cls.get_logger(logger)
        
        if level == "debug":
            log.debug(message)
        elif level == "info":
            log.info(message)
        elif level == "warning":
            log.warning(message)
        elif level == "error":
            log.error(message)
        elif level == "critical":
            log.critical(message)
    
    @classmethod
    def log_command(cls, command, user, guild, options=None):
        """Log a command execution event."""
        guild_text = f"{guild.name} (ID: {guild.id})" if guild else "Direct Message"
        options_text = f" with options {options}" if options else ""
        
        message = f"Command '{command}' executed by {user} (ID: {user.id}) in {guild_text}{options_text}"
        cls.command_logger.info(message)
    
    @classmethod
    def log_error(cls, error, context=None):
        """Log an error with optional context information."""
        context_text = f" in context: {context}" if context else ""
        cls.error_logger.error(f"Error: {error}{context_text}")