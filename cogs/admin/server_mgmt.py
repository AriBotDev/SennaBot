"""
Server management command implementation.
Provides the kill command for server management.
"""
import discord
from discord import app_commands
from discord.ext import commands
import config
from athena.cmd_registry import CommandRegistry
from athena.perm_manager import PermissionManager
from athena.debug_tools import DebugTools
from ..cog_base import BotCog

@CommandRegistry.register_cog("admin")
class ServerManagement(BotCog):
    """Provides the kill command for server management."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.kill]
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user has permission to use the command."""
        # First run the base check
        if not await super().cog_app_command_check(interaction):
            return False
            
        # Then check if user is admin or server owner
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "You need admin permissions to use this command.",
                ephemeral=True
            )
            return False
            
        return True
    
    @app_commands.command(name="kill", description="Have the bot leave this server.")
    async def kill(self, interaction: discord.Interaction):
        """Command for guild owners to make the bot leave the server."""
        # Create confirm view
        view = KillConfirmView(self.bot)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Confirm Bot Removal",
            description="Are you sure you want me to leave this server?",
            color=discord.Color.red()
        )
        
        # Send confirmation
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class KillConfirmView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button):
        # Make sure the person who clicked is the same one who ran the command
        if interaction.user.id != interaction.message.interaction.user.id:
            await interaction.response.send_message("This is not your confirmation dialog.", ephemeral=True)
            return
        
        # Send farewell message
        try:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Farewell",
                    description="Goodbye! I'll be leaving the server now.",
                    color=discord.Color.blue()
                ),
                view=None
            )
        except:
            pass
        
        # Attempt to send a message in a public channel for transparency
        try:
            channel = interaction.channel
            if channel.permissions_for(interaction.guild.me).send_messages:
                await channel.send(
                    embed=discord.Embed(
                        title="Leaving Server",
                        description=f"I've been asked to leave by {interaction.user.mention}. Goodbye!",
                        color=discord.Color.blue()
                    )
                )
        except:
            pass
        
        # Leave the guild
        try:
            await interaction.guild.leave()
        except Exception as e:
            debug = DebugTools.get_debugger("kill_command")
            debug.log(f"Error leaving guild: {e}")
            
            # Send error message if we couldn't leave
            try:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Error",
                        description="I was unable to leave the server. Please try again later or contact the bot owner.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button):
        # Make sure the person who clicked is the same one who ran the command
        if interaction.user.id != interaction.message.interaction.user.id:
            await interaction.response.send_message("This is not your confirmation dialog.", ephemeral=True)
            return
        
        # Cancel the operation
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Cancelled",
                description="Operation cancelled. I'll stay in the server.",
                color=discord.Color.green()
            ),
            view=None
        )