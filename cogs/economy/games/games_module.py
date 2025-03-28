"""
Games module initialization.
Handles setup for game command cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("games_module")

async def setup(bot: commands.Bot):
    """Set up the economy games module."""
    debug.log("Setting up economy games module")
    
    # Import all game cogs
    from .roulette_game import RouletteCog
    from .blackjack_game import BlackjackCog
    from .balance_challenge import BalanceChallengeCog
    
    # Add cogs to bot
    await bot.add_cog(RouletteCog(bot))
    await bot.add_cog(BlackjackCog(bot))
    await bot.add_cog(BalanceChallengeCog(bot))
    
    debug.log("Economy games module setup complete")