"""
Banking module initialization.
Handles setup for banking command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("banking_module")

async def setup(bot: commands.Bot):
    """Set up the economy banking module."""
    debug.log("Setting up economy banking module")
    
    # Import all banking cogs
    from .account_cmds import AccountCog
    from .leaderboard_cmds import LeaderboardCog
    
    # Add cogs to bot
    await bot.add_cog(AccountCog(bot))
    await bot.add_cog(LeaderboardCog(bot))
    
    debug.log("Economy banking module setup complete")