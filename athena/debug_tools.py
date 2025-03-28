import logging
import time
import inspect
import os
from datetime import datetime

class DebugTools:
    """
    Comprehensive debugging utilities for SennaBot development.
    Provides logging, timing, and inspection tools.
    """
    
    _debuggers = {}  # Cache of debugger instances
    _debug_enabled = True  # Global debug toggle
    
    def __init__(self, module_name):
        """Initialize debugger for a specific module."""
        self.module_name = module_name
        self.start_times = {}  # For timing operations
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(f"debug.{module_name}")
        if not self.logger.handlers:
            file_handler = logging.FileHandler("logs/debug.log")
            console_handler = logging.StreamHandler()
            
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.DEBUG)
    
    @classmethod
    def get_debugger(cls, module_name):
        """Get or create a debugger for a module."""
        if module_name not in cls._debuggers:
            cls._debuggers[module_name] = cls(module_name)
        return cls._debuggers[module_name]
    
    @classmethod
    def set_debug_mode(cls, enabled):
        """Globally enable or disable debugging."""
        cls._debug_enabled = enabled
    
    def log(self, message, *args, **kwargs):
        """Log a debug message with context."""
        if not self._debug_enabled:
            return
            
        # Get calling function and line
        frame = inspect.currentframe().f_back
        func_name = frame.f_code.co_name
        line_num = frame.f_lineno
        
        # Format message with any additional arguments
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (Format error: {e}) - Args: {args}, Kwargs: {kwargs}"
        
        # Add context and log
        full_message = f"[{func_name}:{line_num}] {message}"
        self.logger.debug(full_message)
        
        return full_message  # Return for possible further use
    
    def start_timer(self, operation_name):
        """Start timing an operation."""
        if not self._debug_enabled:
            return
        
        self.start_times[operation_name] = time.time()
        self.log(f"Started timer for: {operation_name}")
    
    def end_timer(self, operation_name):
        """End timing an operation and log the duration."""
        if not self._debug_enabled or operation_name not in self.start_times:
            return
        
        elapsed = time.time() - self.start_times[operation_name]
        self.log(f"Operation '{operation_name}' completed in {elapsed:.4f} seconds")
        del self.start_times[operation_name]
        return elapsed
    
    def inspect(self, obj, name=None):
        """Inspect and log an object's details."""
        if not self._debug_enabled:
            return
            
        obj_name = name or "Object"
        self.log(f"Inspecting {obj_name}:")
        
        try:
            # Log type and basic info
            self.log(f"{obj_name} type: {type(obj)}")
            
            # Handle different types
            if isinstance(obj, dict):
                self.log(f"{obj_name} keys: {list(obj.keys())}")
                for key, value in obj.items():
                    self.log(f"{obj_name}[{key}]: {type(value)} = {value}")
            elif isinstance(obj, (list, tuple)):
                self.log(f"{obj_name} length: {len(obj)}")
                for i, item in enumerate(obj[:5]):  # First 5 items
                    self.log(f"{obj_name}[{i}]: {type(item)} = {item}")
                if len(obj) > 5:
                    self.log(f"... ({len(obj) - 5} more items)")
            else:
                # Try to get attributes
                attrs = dir(obj)
                non_magic_attrs = [a for a in attrs if not (a.startswith('__') and a.endswith('__'))]
                self.log(f"{obj_name} has {len(non_magic_attrs)} non-magic attributes")
                for attr in non_magic_attrs[:10]:  # First 10 attributes
                    try:
                        value = getattr(obj, attr)
                        self.log(f"{obj_name}.{attr}: {type(value)}")
                    except Exception as e:
                        self.log(f"Error accessing {obj_name}.{attr}: {e}")
                if len(non_magic_attrs) > 10:
                    self.log(f"... ({len(non_magic_attrs) - 10} more attributes)")
        except Exception as e:
            self.log(f"Error inspecting {obj_name}: {e}")