"""
Command registration and management system.
Centralizes command handling and integration with the permission system.
"""
import discord
from discord import app_commands
from discord.ext import commands
import inspect
import threading
from typing import List, Dict, Callable, Any, Optional, Type, Union
from .debug_tools import DebugTools

# Setup debugger
debug = DebugTools.get_debugger("cmd_registry")

class CommandRegistry:
    """
    Centralized command registration system.
    Manages command categories and guild-specific registration.
    """
    
    # Category-based storage
    _command_map: Dict[str, List[app_commands.Command]] = {}
    _cog_map: Dict[str, List[Type[commands.Cog]]] = {}
    
    # Track registered commands for syncing
    _registered_commands: Dict[str, Dict[str, List[str]]] = {}
    
    # Add lock for thread safety
    _sync_lock = threading.Lock()
    
    @classmethod
    def register_command(cls, category: str) -> Callable:
        """
        Decorator to register a command with a specific category.
        
        Example usage:
        @CommandRegistry.register_command("economy")
        @app_commands.command(name="work", description="Work to earn Medals.")
        async def work_command(self, interaction: discord.Interaction):
            ...
        """
        def decorator(command_func: Callable) -> Callable:
            if category not in cls._command_map:
                cls._command_map[category] = []
            
            # Store the function for later processing
            cls._command_map[category].append(command_func)
            debug.log(f"Registered command {command_func.__name__} in category {category}")
            
            # Return the original function unchanged
            return command_func
        
        return decorator
    
    @classmethod
    def register_cog(cls, category: str) -> Callable:
        """
        Decorator to register a cog class with a specific category.
        
        Example usage:
        @CommandRegistry.register_cog("economy")
        class EconomyWorkCog(EconomyCog):
            ...
        """
        def decorator(cog_class: Type[commands.Cog]) -> Type[commands.Cog]:
            if category not in cls._cog_map:
                cls._cog_map[category] = []
            
            # Store the cog class
            cls._cog_map[category].append(cog_class)
            debug.log(f"Registered cog {cog_class.__name__} in category {category}")
            
            # Return the original class unchanged
            return cog_class
        
        return decorator
    
    @classmethod
    def get_category_commands(cls, category: str) -> List[app_commands.Command]:
        """Get all registered commands for a specific category."""
        return cls._command_map.get(category, [])
    
    @classmethod
    def get_category_cogs(cls, category: str) -> List[Type[commands.Cog]]:
        """Get all registered cog classes for a specific category."""
        return cls._cog_map.get(category, [])
    
    @classmethod
    def _extract_guild_commands(cls, bot: commands.Bot, cog_instance: commands.Cog) -> List[app_commands.Command]:
        """Extract app commands from a cog instance using standard attributes."""
        commands_list = []
        cog_name = cog_instance.__class__.__name__
        
        # Primary method: Use get_app_commands if available
        if hasattr(cog_instance, 'get_app_commands') and callable(getattr(cog_instance, 'get_app_commands')):
            try:
                commands_list = cog_instance.get_app_commands() or []
                debug.log(f"Extracted {len(commands_list)} commands via get_app_commands from {cog_name}")
                return commands_list
            except Exception as e:
                debug.log(f"Error extracting commands via get_app_commands from {cog_name}: {e}")
        
        # Fallback: Check for app_command attributes only if primary method failed
        try:
            for name, method in inspect.getmembers(cog_instance, predicate=inspect.ismethod):
                if hasattr(method, 'app_command') and method.app_command not in commands_list:
                    commands_list.append(method.app_command)
        except Exception as e:
            debug.log(f"Error extracting commands from methods in {cog_name}: {e}")
        
        debug.log(f"Total of {len(commands_list)} commands extracted from cog {cog_name}")
        return commands_list
    
    @classmethod
    async def sync_guild_commands(cls, bot: commands.Bot, guild_id: int, permissions: Dict[str, bool]) -> bool:
        """Sync commands for a specific guild based on permissions."""
        # Acquire lock to prevent race conditions
        with cls._sync_lock:
            guild_id_str = str(guild_id)
            guild_obj = discord.Object(id=guild_id)
            debug.log(f"Syncing commands for guild {guild_id}")
            
            try:
                # Get previously registered commands for this guild
                old_commands = {}
                if guild_id_str in cls._registered_commands:
                    for category, cmd_list in cls._registered_commands[guild_id_str].items():
                        for cmd_name in cmd_list:
                            old_commands[cmd_name] = category
                
                # Clear existing guild commands
                bot.tree.clear_commands(guild=guild_obj)
                debug.log(f"Cleared commands for guild {guild_id}")
                
                # Initialize tracking for this guild
                if guild_id_str not in cls._registered_commands:
                    cls._registered_commands[guild_id_str] = {}
                else:
                    # Clear the old registered commands for this guild
                    cls._registered_commands[guild_id_str] = {}
                
                # Register commands based on permissions
                for category, enabled in permissions.items():
                    if enabled:
                        if category not in cls._registered_commands[guild_id_str]:
                            cls._registered_commands[guild_id_str][category] = []
                        
                        # Get all cogs of this category
                        category_cogs = [
                            cog for cog in bot.cogs.values()
                            if any(isinstance(cog, cog_class) for cog_class in cls.get_category_cogs(category))
                        ]
                        
                        # Extract and register commands from cogs
                        for cog in category_cogs:
                            cog_commands = cls._extract_guild_commands(bot, cog)
                            for command in cog_commands:
                                bot.tree.add_command(command, guild=guild_obj)
                                cls._registered_commands[guild_id_str].setdefault(category, []).append(command.name)
                                if command.name in old_commands:
                                    del old_commands[command.name]  # Remove from old commands as it's still valid
                                debug.log(f"Added command {command.name} to guild {guild_id}")
                
                # Log any commands that were removed
                if old_commands:
                    debug.log(f"Removed old commands from guild {guild_id}: {', '.join(old_commands.keys())}")
                
                # Sync the command tree for this guild
                await bot.tree.sync(guild=guild_obj)
                debug.log(f"Synced command tree for guild {guild_id}")
                
                # Log summary of registered commands
                for category, commands_list in cls._registered_commands[guild_id_str].items():
                    debug.log(f"Guild {guild_id} has {len(commands_list)} {category} commands")
                
                return True
            
            except Exception as e:
                debug.log(f"Error syncing commands for guild {guild_id}: {e}")
                return False
    
    @classmethod
    async def sync_all_guilds(cls, bot: commands.Bot) -> bool:
        """
        Sync commands for all guilds the bot is in.
        Uses PermissionManager to get permissions for each guild.
        """
        from .perm_manager import PermissionManager
        
        debug.log(f"Syncing commands for {len(bot.guilds)} guilds")
        
        success_count = 0
        for guild in bot.guilds:
            # Get permissions for this guild
            guild_permissions = PermissionManager.get_guild_permissions(guild.id)
            
            # Sync commands for this guild
            if await cls.sync_guild_commands(bot, guild.id, guild_permissions):
                success_count += 1
        
        debug.log(f"Successfully synced {success_count}/{len(bot.guilds)} guilds")
        return success_count == len(bot.guilds)