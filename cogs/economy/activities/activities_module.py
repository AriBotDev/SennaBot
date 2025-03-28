"""
Economy activities module initialization.
Handles setup for activity command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("activities_module")

async def setup(bot: commands.Bot):
    """Set up the economy activities module."""
    debug.log("Setting up economy activities module")
    
    # Import all activity cogs
    from .work_cmds import WorkCog
    from .crime_cmds import CrimeCog
    from .rob_cmds import RobCog
    
    # Add cogs to bot
    await bot.add_cog(WorkCog(bot))
    await bot.add_cog(CrimeCog(bot))
    await bot.add_cog(RobCog(bot))
    
    debug.log("Economy activities module setup complete")