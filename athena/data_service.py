"""
Unified data management layer for SennaBot.
Provides consistent access to all persistent data with caching and error handling.
"""
import os
import json
import time
import shutil
from .debug_tools import DebugTools
import threading

# Setup debugger
debug = DebugTools.get_debugger("data_service")
_cache_timestamps = {}
CACHE_TTL = 300  # 5 minutes

class DataService:
    """
    Centralized data management for the bot.
    Handles loading, saving, and caching of all persistent data.
    """
    
    # Constants
    DATA_DIR = "data"
    GUILDS_DIR = os.path.join(DATA_DIR, "guilds")
    CONFIG_DIR = os.path.join(DATA_DIR, "config")
    RESPONSES_DIR = os.path.join(DATA_DIR, "responses")
    
    # In-memory caches
    _guild_cache = {}
    _response_cache = {}
    _config_cache = {}
    _guild_locks = {}

    @classmethod
    def get_guild_lock(cls, guild_id):
        """Get or create a lock for a specific guild."""
        guild_id = str(guild_id)
        if guild_id not in cls._guild_locks:
            cls._guild_locks[guild_id] = threading.Lock()
        return cls._guild_locks[guild_id]
    
    @classmethod
    def initialize(cls):
        """Initialize the data service."""
        debug.log("Initializing DataService")
        cls._ensure_directories()
        
        # Pre-load config data
        cls._load_bot_settings()
        
        debug.log("DataService initialization complete")
    
    @classmethod
    def _ensure_directories(cls):
        """Ensure all data directories exist."""
        os.makedirs(cls.GUILDS_DIR, exist_ok=True)
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        os.makedirs(cls.RESPONSES_DIR, exist_ok=True)
    
    @classmethod
    def _load_bot_settings(cls):
        """Load global bot settings."""
        settings_file = os.path.join(cls.CONFIG_DIR, "bot_settings.json")
        
        if not os.path.exists(settings_file):
            # Create default settings
            default_settings = {
                "version": "1.0.0",
                "debug_mode": True,
                "starting_balance": 50,
                "critical_success_chance": 2,
                "critical_multiplier_min": 3,
                "critical_multiplier_max": 5
            }
            cls._safe_save_json(settings_file, default_settings)
            cls._config_cache["bot_settings"] = default_settings
        else:
            cls._config_cache["bot_settings"] = cls._safe_load_json(settings_file, {})
    
    @classmethod
    def _safe_load_json(cls, file_path, default=None):
        """Safely load a JSON file with error handling."""
        default = {} if default is None else default
        debug.start_timer(f"load_json_{os.path.basename(file_path)}")
        
        try:
            if not os.path.exists(file_path):
                debug.log(f"File not found: {file_path}")
                return default
                
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                debug.log(f"Successfully loaded data from {file_path}")
                return data
                
        except json.JSONDecodeError as e:
            debug.log(f"JSON decode error in {file_path}: {e}")
            
            # Try to load backup if exists
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                debug.log(f"Attempting to restore from backup: {backup_path}")
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        debug.log(f"Successfully restored from backup")
                        return data
                except Exception as be:
                    debug.log(f"Backup restore failed: {be}")
            
            return default
            
        except Exception as e:
            debug.log(f"Error loading {file_path}: {e}")
            return default
            
        finally:
            debug.end_timer(f"load_json_{os.path.basename(file_path)}")
    
    @classmethod
    def _safe_save_json(cls, file_path, data):
        """Safely save data to a JSON file with atomic writes."""
        cls._ensure_directories()
        debug.start_timer(f"save_json_{os.path.basename(file_path)}")
        
        # Create backup of existing file
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                shutil.copy2(file_path, backup_path)
                debug.log(f"Created backup at {backup_path}")
            except Exception as e:
                debug.log(f"Error creating backup: {e}")
        
        # Write to temporary file first
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                # Write data
                json.dump(data, f, indent=4)
                # Ensure data is flushed to disk
                f.flush()
                os.fsync(f.fileno())
            
            # Rename temp file to actual file (atomic operation)
            os.replace(temp_path, file_path)
            debug.log(f"Successfully saved data to {file_path}")
            return True
            
        except Exception as e:
            debug.log(f"Error saving to {file_path}: {e}")
            return False
            
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            debug.end_timer(f"save_json_{os.path.basename(file_path)}")
    
    @classmethod
    def load_guild_data(cls, guild_id, force_reload=False):
        """Load data for a specific guild with TTL caching."""
        guild_id = str(guild_id)
        debug.log(f"Loading guild data for {guild_id}")
        
        current_time = time.time()
        
        # Check if cache is valid
        cache_valid = (
            guild_id in cls._guild_cache and
            guild_id in cls._cache_timestamps and
            current_time - cls._cache_timestamps[guild_id] < CACHE_TTL and
            not force_reload
        )
        
        if cache_valid:
            debug.log(f"Using cached data for guild {guild_id}")
            return cls._guild_cache[guild_id].copy()  # Return a copy to avoid race conditions
        
        # Load from file
        file_path = os.path.join(cls.GUILDS_DIR, f"{guild_id}.json")
        data = cls._safe_load_json(file_path, {})
        
        # Update cache and timestamp
        cls._guild_cache[guild_id] = data.copy()
        cls._cache_timestamps[guild_id] = current_time
        
        return data
    
    @classmethod
    def invalidate_cache(cls, guild_id=None):
        """Invalidate cache for a specific guild or all guilds."""
        if guild_id:
            guild_id = str(guild_id)
            if guild_id in cls._guild_cache:
                del cls._guild_cache[guild_id]
                if guild_id in cls._cache_timestamps:
                    del cls._cache_timestamps[guild_id]
                debug.log(f"Invalidated cache for guild {guild_id}")
        else:
            cls._guild_cache.clear()
            cls._cache_timestamps.clear()
            debug.log("Invalidated all data caches")
    
    @classmethod
    def save_guild_data(cls, guild_id, data):
        """Save data for a specific guild with locking."""
        guild_id = str(guild_id)
        debug.log(f"Saving guild data for {guild_id}")
        
        # Acquire lock for this guild
        with cls.get_guild_lock(guild_id):
            # Update cache
            cls._guild_cache[guild_id] = data.copy()
            
            # Save to file
            file_path = os.path.join(cls.GUILDS_DIR, f"{guild_id}.json")
            return cls._safe_save_json(file_path, data)
    
    @classmethod
    def get_user_data(cls, guild_id, user_id, username=None):
        """
        Get user data with automatic initialization.
        Creates default user entry if none exists.
        """
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        guild_data = cls.load_guild_data(guild_id)
        
        if user_id not in guild_data:
            debug.log(f"Creating new user data for {user_id} in guild {guild_id}")
            guild_data[user_id] = cls.create_default_user(user_id, username)
            cls.save_guild_data(guild_id, guild_data)
        
        return guild_data[user_id]
    
    @classmethod
    def create_default_user(cls, user_id, username=None):
        """Create default user data structure."""
        # Get the starting balance from settings
        starting_balance = cls._config_cache.get("bot_settings", {}).get("starting_balance", 50)
        
        # Convert to int for storage consistency
        try:
            numeric_id = int(user_id)
        except:
            numeric_id = 0
        
        return {
            "user_id": numeric_id,
            "username": username or f"User_{user_id}",
            "pockets": 0,
            "savings": starting_balance,
            "cooldowns": {
                "work": 0, "crime": 0, "rob": 0, 
                "roulette": 0, "escape": 0, "breakout": 0
            },
            "injured": False,
            "injuries": 0,
            "prison": None,
            "last_robbed": 0
        }
    
    @classmethod
    def get_bot_setting(cls, setting_name, default=None):
        """Get a specific bot setting from the config."""
        return cls._config_cache.get("bot_settings", {}).get(setting_name, default)
    
    @classmethod
    def set_bot_setting(cls, setting_name, value):
        """Set a specific bot setting in the config."""
        settings = cls._config_cache.get("bot_settings", {})
        settings[setting_name] = value
        cls._config_cache["bot_settings"] = settings
        
        # Save to file
        settings_file = os.path.join(cls.CONFIG_DIR, "bot_settings.json")
        return cls._safe_save_json(settings_file, settings)
    
    @classmethod
    def load_response_data(cls, category):
        """Load response data for a specific category."""
        if category in cls._response_cache:
            return cls._response_cache[category]
        
        file_path = os.path.join(cls.RESPONSES_DIR, f"{category}_responses.json")
        data = cls._safe_load_json(file_path, {})
        
        # Cache and return data
        cls._response_cache[category] = data
        return data
    
    @classmethod
    def clear_cache(cls, guild_id=None):
        """Clear the cache for a specific guild or all guilds."""
        if guild_id:
            guild_id = str(guild_id)
            if guild_id in cls._guild_cache:
                del cls._guild_cache[guild_id]
                debug.log(f"Cleared cache for guild {guild_id}")
        else:
            cls._guild_cache.clear()
            cls._response_cache.clear()
            debug.log("Cleared all data caches")