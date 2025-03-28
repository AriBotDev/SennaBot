"""
Admin module initialization.
Handles setup for admin command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("admin_module")

async def setup(bot: commands.Bot):
    """Set up the admin module."""
    debug.log("Setting up admin module")
    
    # Import all admin cogs
    from .owner_cmds import OwnerCommands
    from .server_mgmt import ServerManagement
    from .owner_eco_cmds import OwnerEconomyCommands
    
    # Add cogs to bot
    await bot.add_cog(OwnerCommands(bot))
    await bot.add_cog(ServerManagement(bot))
    await bot.add_cog(OwnerEconomyCommands(bot))
    
    debug.log("Admin module setup complete")