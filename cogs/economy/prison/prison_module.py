"""
Prison module initialization.
Handles setup for prison-related command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("prison_module")

async def setup(bot: commands.Bot):
    """Set up the economy prison module."""
    debug.log("Setting up economy prison module")
    
    # Import all prison-related cogs
    from .prison_system import PrisonSystem
    from .escape_cmds import EscapeCommands
    from .breakout_cmds import BreakoutCommands
    
    # Add cogs to bot
    await bot.add_cog(PrisonSystem(bot))
    await bot.add_cog(EscapeCommands(bot))
    await bot.add_cog(BreakoutCommands(bot))
    
    debug.log("Economy prison module setup complete")