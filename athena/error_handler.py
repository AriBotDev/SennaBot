"""
Error handling system for SennaBot.
Provides centralized error handling, logging, and user feedback.
"""
import discord
import traceback
import sys
import asyncio
import functools
from .debug_tools import DebugTools

# Setup debugger
debug = DebugTools.get_debugger("error_handler")

class ErrorHandler:
    """
    Centralized error handling for the bot.
    Handles logging, user feedback, and recovery.
    """
    
    # Error categories
    PERMISSION_ERRORS = (
        discord.app_commands.errors.CommandNotFound,
        discord.errors.Forbidden,
        discord.app_commands.errors.MissingPermissions
    )
    
    USER_ERRORS = (
        discord.app_commands.errors.CommandOnCooldown,
        discord.app_commands.errors.MissingRequiredArgument
    )
    
    # Reporting settings
    _report_to_owner = True
    _owner_id = None
    
    @classmethod
    def set_owner_id(cls, owner_id):
        """Set the owner ID for error reporting."""
        cls._owner_id = owner_id
    
    @classmethod
    async def handle_command_error(cls, interaction, error):
        """
        Handle an error from a slash command.
        Logs the error and provides user feedback.
        """
        debug.log(f"Command error: {error}")
        
        # Unwrap CommandInvokeError
        if isinstance(error, discord.app_commands.errors.CommandInvokeError):
            error = error.original
        
        # Handle different error types
        if isinstance(error, cls.PERMISSION_ERRORS):
            return await cls._handle_permission_error(interaction, error)
        elif isinstance(error, cls.USER_ERRORS):
            return await cls._handle_user_error(interaction, error)
        else:
            return await cls._handle_unknown_error(interaction, error)
    
    @classmethod
    async def _handle_permission_error(cls, interaction, error):
        """Handle permission and command not found errors."""
        # Handle whitelist-related errors
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            message = "This command is not available in this server."
        elif isinstance(error, discord.errors.Forbidden):
            message = "I don't have permission to do that!"
        else:
            message = "You don't have permission to use this command."
        
        # Send ephemeral response
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            debug.log(f"Error sending permission error response: {e}")
        
        # Log the error
        debug.log(f"Permission error: {error}")
    
    @classmethod
    async def _handle_user_error(cls, interaction, error):
        """Handle user input errors like cooldowns."""
        # Handle cooldown errors
        if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
            message = f"This command is on cooldown! Try again in {error.retry_after:.1f} seconds."
        # Handle missing arguments
        elif isinstance(error, discord.app_commands.errors.MissingRequiredArgument):
            message = f"Missing required argument: {error.param.name}"
        else:
            message = str(error)
        
        # Send ephemeral response
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            debug.log(f"Error sending user error response: {e}")
        
        # Log the error
        debug.log(f"User error: {error}")
    
    @classmethod
    async def _handle_unknown_error(cls, interaction, error):
        """Handle unexpected errors with detailed logging."""
        # Get full traceback
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        debug.log(f"Unexpected error: {error}\n{tb}")
        
        # Send gentle error message to user
        user_message = "An unexpected error occurred. The bot owner has been notified."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(user_message, ephemeral=True)
            else:
                await interaction.response.send_message(user_message, ephemeral=True)
        except Exception as e:
            debug.log(f"Error sending unknown error response: {e}")
        
        # Report to owner if enabled
        if cls._report_to_owner and cls._owner_id:
            # Create detailed error report
            command_name = interaction.command.name if interaction.command else "Unknown"
            guild_name = interaction.guild.name if interaction.guild else "DM"
            guild_id = interaction.guild.id if interaction.guild else "N/A"
            user_name = interaction.user.name
            user_id = interaction.user.id
            
            error_report = (
                f"**Error in command `{command_name}`**\n"
                f"**Guild:** {guild_name} (ID: {guild_id})\n"
                f"**User:** {user_name} (ID: {user_id})\n"
                f"**Error:** ```{error}```\n"
            )
            
            # Include traceback if it's not too long
            if len(tb) <= 1900:
                error_report += f"**Traceback:**```{tb}```"
            else:
                error_report += f"**Traceback: (first 1900 chars)**```{tb[:1900]}...```"
            
            # Send report to owner with retry mechanism
            await cls._send_error_to_owner(interaction.client, error_report)
    
    @classmethod
    def handle_event_error(cls, event_name, error, extra_context=None):
        """
        Handle an error from an event.
        Logs the error but doesn't provide user feedback.
        """
        # Get full traceback
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        context = f" | Context: {extra_context}" if extra_context else ""
        debug.log(f"Event error in {event_name}{context}: {error}\n{tb}")
        
        # Report to owner if enabled and we have a bot instance to use
        if cls._report_to_owner and cls._owner_id and hasattr(cls, '_bot_instance'):
            # Create error report
            error_report = (
                f"**Error in event `{event_name}`**\n"
                f"**Context:** {extra_context or 'None provided'}\n"
                f"**Error:** ```{error}```\n"
            )
            
            # Include traceback if it's not too long
            if len(tb) <= 1900:
                error_report += f"**Traceback:**```{tb}```"
            else:
                error_report += f"**Traceback: (first 1900 chars)**```{tb[:1900]}...```"
            
            # Schedule the report to be sent
            asyncio.create_task(cls._send_error_to_owner(cls._bot_instance, error_report))
        else:
            debug.log(f"Error in {event_name} should be reported to owner (when bot instance is available)")

    @classmethod
    async def handle_cog_error(cls, cog, interaction, error, command_name=None):
        """Handle an error from a cog command."""
        # Get command name if not provided
        if command_name is None and hasattr(interaction, 'command'):
            command_name = interaction.command.name
        
        # Log the error
        cog.debug.log(f"Error in {command_name}: {error}")
        
        try:
            if isinstance(error, cls.PERMISSION_ERRORS):
                message = "You don't have permission to use this command."
                await cog.send_embed(interaction, "Permission Error", message, discord.Color.red(), ephemeral=True)
            elif isinstance(error, cls.USER_ERRORS):
                if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
                    message = f"This command is on cooldown! Try again in {error.retry_after:.1f} seconds."
                else:
                    message = str(error)
                await cog.send_embed(interaction, "Command Error", message, discord.Color.orange(), ephemeral=True)
            else:
                # Handle unexpected errors
                await cog.send_embed(
                    interaction, 
                    "Error", 
                    "An unexpected error occurred. The bot owner has been notified.",
                    discord.Color.red(),
                    ephemeral=True
                )
                
                # Report to owner if enabled
                cls._report_to_owner_from_cog(cog, interaction, error, command_name)
        except Exception as e:
            cog.debug.log(f"Error handling error: {e}")
        
        return False

    @classmethod
    def _report_to_owner_from_cog(cls, cog, interaction, error, command_name):
        """Report error to owner from cog context."""
        if cls._report_to_owner and cls._owner_id and hasattr(cog, 'bot'):
            try:
                # Get full traceback
                tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                
                # Create detailed error report
                guild_name = interaction.guild.name if interaction.guild else "DM"
                guild_id = interaction.guild.id if interaction.guild else "N/A"
                user_name = interaction.user.name
                user_id = interaction.user.id
                
                error_report = (
                    f"**Error in command `{command_name}`**\n"
                    f"**Cog:** {cog.__class__.__name__}\n"
                    f"**Guild:** {guild_name} (ID: {guild_id})\n"
                    f"**User:** {user_name} (ID: {user_id})\n"
                    f"**Error:** ```{error}```\n"
                )
                
                # Include traceback if it's not too long
                if len(tb) <= 1900:
                    error_report += f"**Traceback:**```{tb}```"
                else:
                    error_report += f"**Traceback: (first 1900 chars)**```{tb[:1900]}...```"
                
                # Schedule the reporting to avoid blocking
                cog.bot.loop.create_task(cls._send_error_to_owner(cog.bot, error_report))
            except Exception as e:
                cog.debug.log(f"Error reporting to owner: {e}")

    @classmethod
    async def _send_error_to_owner(cls, bot, error_report):
        """Send error report to owner with retry and logging."""
        if not cls._owner_id:
            debug.log("No owner ID set for error reporting")
            return False
            
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                owner = await bot.fetch_user(cls._owner_id)
                if not owner:
                    debug.log(f"Could not find owner with ID {cls._owner_id}")
                    return False
                    
                await owner.send(error_report)
                debug.log(f"Error report sent to owner: {error_report[:50]}...")
                return True
                
            except discord.HTTPException as e:
                debug.log(f"HTTP error sending to owner (retry {retry_count+1}/{max_retries}): {e}")
                retry_count += 1
                await asyncio.sleep(1)  # Wait before retry
                
            except Exception as e:
                debug.log(f"Unexpected error sending to owner: {e}")
                return False
        
        debug.log(f"Failed to send error to owner after {max_retries} attempts")
        return False
    
    @classmethod
    def set_bot_instance(cls, bot):
        """Set a bot instance to use for event error reporting."""
        cls._bot_instance = bot
        debug.log("Bot instance set for error reporting")
    
    def command_error_handler(func):
        """Decorator for standardized command error handling."""
        @functools.wraps(func)
        async def wrapper(self, interaction, *args, **kwargs):
            try:
                return await func(self, interaction, *args, **kwargs)
            except Exception as e:
                # Get command name
                command_name = func.__name__
                
                # Log the error
                if hasattr(self, 'debug'):
                    self.debug.log(f"Error in {command_name}: {e}")
                else:
                    debug = DebugTools.get_debugger("error_handler")
                    debug.log(f"Error in {command_name}: {e}")
                
                try:
                    # Send error message to user
                    if hasattr(self, 'send_embed'):
                        await self.send_embed(
                            interaction,
                            "Error",
                            "An error occurred while processing this command. The bot owner has been notified.",
                            discord.Color.red(),
                            ephemeral=True
                        )
                    else:
                        if interaction.response.is_done():
                            await interaction.followup.send(
                                "An error occurred while processing this command.",
                                ephemeral=True
                            )
                        else:
                            await interaction.response.send_message(
                                "An error occurred while processing this command.",
                                ephemeral=True
                            )
                except Exception as response_error:
                    # If response failed, try followup as a last resort
                    try:
                        await interaction.followup.send(
                            "An error occurred while processing this command.",
                            ephemeral=True
                        )
                    except:
                        debug.log("Failed to send any error response to user")
                
                # Report to owner
                from athena.error_handler import ErrorHandler
                if hasattr(self, 'bot'):
                    ErrorHandler._report_to_owner_from_cog(self, interaction, e, command_name)
                else:
                    ErrorHandler.handle_command_error(interaction, e)
                
                # Rethrow specific exceptions we want to bubble up
                if isinstance(e, (commands.CommandNotFound, commands.MissingRequiredArgument)):
                    raise
        
        return wrapper
    