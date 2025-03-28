"""
Core initialization module for Athena framework.
Provides central access to all framework components and manages initialization.
"""
import os
import sys
import logging

class Athena:
    """Main framework class that coordinates all components."""
    
    # Framework version
    VERSION = "1.0.0"
    
    # Flag to track initialization
    initialized = False
    
    # Component references - will be populated during initialization
    data_service = None
    perm_manager = None
    cmd_registry = None
    response_manager = None
    error_handler = None
    logging_service = None
    
    @classmethod
    def initialize(cls):
        """Initialize the Athena framework."""
        if cls.initialized:
            print("Athena framework already initialized")
            return
        
        print(f"Initializing Athena framework v{cls.VERSION}")
        
        # Ensure data directories exist
        cls._ensure_directories()
        
        # Import and initialize components
        from .debug_tools import DebugTools
        cls.debug = DebugTools.get_debugger("framework")
        cls.debug.log(f"Initializing Athena framework v{cls.VERSION}")
        
        # Import and set up logging first
        from .logging_service import LoggingService
        cls.logging_service = LoggingService
        cls.logging_service.initialize()
        
        # Import other components
        from .data_service import DataService
        from .perm_manager import PermissionManager
        from .cmd_registry import CommandRegistry
        from .response_manager import ResponseManager
        from .error_handler import ErrorHandler
        
        # Store references
        cls.data_service = DataService
        cls.perm_manager = PermissionManager
        cls.cmd_registry = CommandRegistry
        cls.response_manager = ResponseManager
        cls.error_handler = ErrorHandler
        
        # Initialize components that need it
        cls.data_service.initialize()
        cls.response_manager.initialize()
        
        cls.initialized = True
        cls.debug.log("Athena framework initialization complete")
    
    @classmethod
    def _ensure_directories(cls):
        """Ensure all required directories exist."""
        directories = [
            "data",
            "data/config",
            "data/guilds",
            "data/responses",
            "logs",
            "dm_logs"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
    
    @classmethod
    def shutdown(cls):
        """Perform cleanup operations before shutdown."""
        if not cls.initialized:
            return
            
        if hasattr(cls, 'debug'):
            cls.debug.log("Shutting down Athena framework")
        
        # Add any cleanup needed here
        
        cls.initialized = False