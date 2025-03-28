"""
Economy module initialization.
Handles setup for economy cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.cmd_registry import CommandRegistry

# Setup debugger
debug = DebugTools.get_debugger("economy_module")

async def setup(bot: commands.Bot):
    """Set up the economy module."""
    debug.log("Setting up economy module")
    
    # Load submodules
    submodules = [
        "cogs.economy.activities.activities_module",
        "cogs.economy.banking.banking_module",
        "cogs.economy.games.games_module",
        "cogs.economy.prison.prison_module",
        "cogs.economy.status.status_module",
    ]
    
    for submodule in submodules:
        try:
            await bot.load_extension(submodule)
            debug.log(f"Loaded economy submodule: {submodule}")
        except Exception as e:
            debug.log(f"Error loading economy submodule {submodule}: {e}")
    
    debug.log("Economy module setup complete")