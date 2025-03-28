"""
Status module initialization.
Handles setup for status-related command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools

# Setup debugger
debug = DebugTools.get_debugger("status_module")

async def setup(bot: commands.Bot):
    """Set up the economy status module."""
    debug.log("Setting up economy status module")
    
    # Import all status-related cogs
    from .injury_system import InjuryCommands
    from .mortician_cmds import MorticianCommands
    
    # Add cogs to bot
    await bot.add_cog(InjuryCommands(bot))
    await bot.add_cog(MorticianCommands(bot))
    
    debug.log("Economy status module setup complete")