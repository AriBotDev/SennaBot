"""
Main bot file for SennaBot.
Handles initialization, event handling, and command processing.
"""
import discord
import logging
import os
import asyncio
import time
import config
import re
from discord.ext import commands

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Initialize Athena framework
from athena.framework_core import Athena
Athena.initialize()

# Access framework components
from athena.debug_tools import DebugTools
from athena.logging_service import LoggingService
from athena.perm_manager import PermissionManager
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.error_handler import ErrorHandler
from athena.response_manager import ResponseManager

# Create debugger
debug = DebugTools.get_debugger("bot")
logger = LoggingService.get_logger("main")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents, auto_sync_commands=False)

# Set owner ID in error handler
ErrorHandler.set_owner_id(config.OWNER_ID)

# Helper function for logging
def sanitize_filename(name: str) -> str:
    """Sanitize a filename to be safe for the filesystem."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '', name)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    try:
        logger.info(f"✅ Logged in as {bot.user}!")
        debug.log(f"Bot is ready as {bot.user}!")
        print(f"✅ Logged in as {bot.user}!")
        
        # Create guild permission entries for all guilds
        for guild in bot.guilds:
            PermissionManager.ensure_guild_entry(
                PermissionManager.load_permissions(),
                str(guild.id),
                guild.name
            )
        PermissionManager.save_permissions()
        
        # Load all cogs
        debug.log("Loading cogs...")
        await bot.load_extension("cogs")
        
        # Clear global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        debug.log("Cleared global commands")
        
        # Sync commands for all guilds
        await CommandRegistry.sync_all_guilds(bot)
        
        # Process any prisoners who should be released
        await process_prison_releases()
        
        logger.info("Bot initialization complete")
        debug.log("Bot initialization complete")
    except Exception as e:
        logger.error(f"Error during bot initialization: {e}")
        debug.log(f"Error during bot initialization: {e}")

async def process_prison_releases():
    """Process any prisoners who should be released."""
    debug.log("Processing prison releases")
    
    try:
        current_time = int(time.time())
        processed_count = 0
        
        for guild in bot.guilds:
            guild_data = DataService.load_guild_data(guild.id)
            updated = False
            
            for user_id, user_data in guild_data.items():
                if not user_id.isdigit():
                    continue  # Skip non-user entries
                    
                prison = user_data.get("prison")
                if prison:
                    release_time = prison.get('release_time', 0)
                    
                    # Check if prison time is up
                    if current_time >= release_time:
                        # Auto-release from prison
                        guild_data[user_id]["prison"] = None
                        updated = True
                        processed_count += 1
                        
                        # Try to message the user about being released
                        try:
                            member = guild.get_member(int(user_id))
                            if member:
                                release_msg = f"You have served your time and have been released from hell..."
                                embed = discord.Embed(
                                    title="Prison Release", 
                                    description=release_msg,
                                    color=discord.Color.green()
                                )
                                await member.send(embed=embed)
                        except Exception as e:
                            debug.log(f"Failed to send prison release DM: {e}")
            
            if updated:
                DataService.save_guild_data(guild.id, guild_data)
        
        debug.log(f"Released {processed_count} prisoners")
    except Exception as e:
        debug.log(f"Error processing prison releases: {e}")

@bot.event
async def on_message(message):
    """Event handler for all messages."""
    try:
        # Process commands first
        await bot.process_commands(message)
        
        # Handle DM logging
        if message.guild is None and not message.author.bot:
            # Log the DM
            username = message.author.name.replace(" ", "_")
            os.makedirs("dm_logs", exist_ok=True)
            log_filename = f"dm_logs/{username}_{message.author.id}.txt"
            
            log_entry = f"[{message.created_at}] {message.author} (ID: {message.author.id}): {message.content}\n"
            
            with open(log_filename, "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
            
            # Forward to owner if not the owner
            if message.author.id != config.OWNER_ID:
                try:
                    owner = await bot.fetch_user(config.OWNER_ID)
                    if owner:
                        await owner.send(f"📩 DM from {message.author} (ID: {message.author.id}):\n{message.content}")
                except Exception as e:
                    debug.log(f"Error forwarding DM to owner: {e}")
    except Exception as e:
        logger.error(f"Error in on_message event: {e}")
        ErrorHandler.handle_event_error("on_message", e, {"author": message.author.id})

@bot.event
async def on_guild_join(guild):
    """Called when the bot joins a new guild."""
    try:
        logger.info(f"Bot added to guild: {guild.name} (ID: {guild.id})")
        debug.log(f"Bot added to guild: {guild.name} (ID: {guild.id})")
        
        # Create permission entry for this guild
        PermissionManager.ensure_guild_entry(
            PermissionManager.load_permissions(),
            str(guild.id),
            guild.name
        )
        PermissionManager.save_permissions()
        
        # Sync commands for this guild
        guild_permissions = PermissionManager.get_guild_permissions(guild.id)
        await CommandRegistry.sync_guild_commands(bot, guild.id, guild_permissions)
    except Exception as e:
        logger.error(f"Error in on_guild_join event: {e}")
        ErrorHandler.handle_event_error("on_guild_join", e, {"guild_id": guild.id, "guild_name": guild.name})

@bot.event
async def on_guild_remove(guild):
    """Called when the bot is removed from a guild."""
    try:
        logger.info(f"Bot removed from guild: {guild.name} (ID: {guild.id})")
        debug.log(f"Bot removed from guild: {guild.name} (ID: {guild.id})")
    except Exception as e:
        logger.error(f"Error in on_guild_remove event: {e}")
        ErrorHandler.handle_event_error("on_guild_remove", e, {"guild_id": guild.id})

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Global error handler for app commands."""
    await ErrorHandler.handle_command_error(interaction, error)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.critical(f"Fatal error running bot: {e}")
        debug.log(f"Fatal error running bot: {e}")
    finally:
        # Shutdown Athena framework
        Athena.shutdown()