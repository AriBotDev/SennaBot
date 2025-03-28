"""
General module initialization.
Handles setup for general command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("general_module")

async def setup(bot: commands.Bot):
    """Set up the general module."""
    debug.log("Setting up general module")
    
    # Import all general cogs
    from .social_cmds import SocialCommands
    from .utility_cmds import UtilityCommands
    
    # Add cogs to bot
    await bot.add_cog(SocialCommands(bot))
    await bot.add_cog(UtilityCommands(bot))
    
    debug.log("General module setup complete")