"""
Permission management system for SennaBot.
Handles guild-specific permissions for command categories.
"""
import os
import json
from .debug_tools import DebugTools
from .data_service import DataService

# Setup debugger
debug = DebugTools.get_debugger("perm_manager")

class PermissionManager:
    """
    Enhanced permission system for controlling command access.
    """
    
    # Constants
    OWNER_GUILD_ID = "1349273253343920210"
    PERMISSIONS_FILE = os.path.join("data", "config", "guild_permissions.json")
    
    # Core settings
    ALLOWED_CATEGORIES = ["general", "economy", "admin"]
    CATEGORY_DESCRIPTIONS = {
        "general": "Basic utility commands like headpats, gdtrello",
        "economy": "Economy system with currency, games, and status",
        "admin": "Administrative commands for bot management"
    }
    
    # Cache
    _permissions_cache = None
    
    @classmethod
    def load_permissions(cls, force_reload=False):
        """Load permissions data with caching."""
        # Return cached data if available and not forcing reload
        if cls._permissions_cache is not None and not force_reload:
            return cls._permissions_cache.copy()  # Return a copy to prevent direct modification
        
        debug.log("Loading permissions data")
        
        # Load the permissions file
        if os.path.exists(cls.PERMISSIONS_FILE):
            try:
                with open(cls.PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                    permissions = json.load(f)
                    debug.log(f"Loaded permissions from {cls.PERMISSIONS_FILE}")
            except json.JSONDecodeError:
                debug.log(f"Error decoding {cls.PERMISSIONS_FILE}, creating new")
                permissions = {}
            except Exception as e:
                debug.log(f"Error loading {cls.PERMISSIONS_FILE}: {e}")
                permissions = {}
        else:
            debug.log("No permissions file found, creating new")
            permissions = {}
        
        # Ensure owner guild has all permissions
        owner_entry = cls.ensure_guild_entry(permissions, cls.OWNER_GUILD_ID, "Owner Guild")
        for category in cls.ALLOWED_CATEGORIES:
            owner_entry[category] = True
        
        # Cache and return
        cls._permissions_cache = permissions.copy()
        return permissions
    
    @classmethod
    def save_permissions(cls, permissions=None):
        """Save permissions data."""
        debug.log("Saving permissions data")
        
        # Use provided permissions or the cached ones
        if permissions is None:
            permissions = cls._permissions_cache
            if permissions is None:
                permissions = {}
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(cls.PERMISSIONS_FILE), exist_ok=True)
        
        # Save to file
        try:
            # Write to temp file first
            temp_file = f"{cls.PERMISSIONS_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(permissions, f, indent=4)
            
            # Replace original with temp file (atomic operation)
            os.replace(temp_file, cls.PERMISSIONS_FILE)
            debug.log(f"Saved permissions to {cls.PERMISSIONS_FILE}")
            
            # Update cache
            cls._permissions_cache = permissions
            return True
        except Exception as e:
            debug.log(f"Error saving permissions: {e}")
            return False
    
    @classmethod
    def ensure_guild_entry(cls, permissions, guild_id, guild_name=None):
        """
        Ensure a guild has an entry in the permissions data.
        Creates default entry if none exists.
        """
        guild_id = str(guild_id)
        
        if guild_id not in permissions:
            debug.log(f"Creating new permissions entry for guild {guild_id}")
            permissions[guild_id] = {"server_name": guild_name or f"Guild_{guild_id}"}
        
        # Add missing categories with default value False
        for category in cls.ALLOWED_CATEGORIES:
            if category not in permissions[guild_id]:
                # Special case for owner guild
                if guild_id == cls.OWNER_GUILD_ID:
                    permissions[guild_id][category] = True
                else:
                    permissions[guild_id][category] = False
        
        # Update server name if provided and different
        if guild_name and permissions[guild_id].get("server_name") != guild_name:
            permissions[guild_id]["server_name"] = guild_name
        
        return permissions[guild_id]
    
    @classmethod
    def get_guild_permission(cls, guild_id, category):
        """
        Check if a guild has permission for a specific category.
        Owner guild always has permission for all categories.
        """
        guild_id = str(guild_id)
        
        # Owner guild always has permission
        if guild_id == cls.OWNER_GUILD_ID:
            return True
        
        # Load permissions
        permissions = cls.load_permissions()
        
        # Check if guild has entry and category
        if guild_id in permissions:
            return permissions[guild_id].get(category, False)
        
        return False
    
    @classmethod
    def update_permission(cls, guild_id, category, enabled, guild_name=None):
        """
        Update a guild's permission for a specific category.
        Creates guild entry if it doesn't exist.
        """
        guild_id = str(guild_id)
        
        if category not in cls.ALLOWED_CATEGORIES:
            debug.log(f"Invalid category: {category}")
            return False
        
        # Load permissions
        permissions = cls.load_permissions()
        
        # Ensure guild entry exists
        guild_entry = cls.ensure_guild_entry(permissions, guild_id, guild_name)
        
        # Update permission
        guild_entry[category] = bool(enabled)
        
        # Save permissions
        return cls.save_permissions(permissions)
    
    @classmethod
    def get_category_guilds(cls, category):
        """
        Get list of guild IDs that have permission for a specific category.
        Returns list of guild IDs as strings.
        """
        permissions = cls.load_permissions()
        
        return [
            gid for gid, info in permissions.items()
            if info.get(category, False)
        ]
    
    @classmethod
    def get_guild_permissions(cls, guild_id):
        """
        Get all permissions for a specific guild.
        Returns dict of category -> bool.
        """
        guild_id = str(guild_id)
        permissions = cls.load_permissions()
        
        if guild_id not in permissions:
            return {category: False for category in cls.ALLOWED_CATEGORIES}
        
        return {
            category: permissions[guild_id].get(category, False)
            for category in cls.ALLOWED_CATEGORIES
        }