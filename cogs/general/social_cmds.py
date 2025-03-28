"""
Social commands implementation.
Provides fun social interaction commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
import config
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ..cog_base import BotCog

@CommandRegistry.register_cog("general")
class SocialCommands(BotCog):
    """Provides social interaction commands."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.toggle_headpats]
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user has permission to use the command."""
        # First run the base check
        if not await super().cog_app_command_check(interaction):
            return False
            
        # Then check if guild has general permission
        from athena.perm_manager import PermissionManager
        if not PermissionManager.get_guild_permission(interaction.guild.id, "general"):
            await interaction.response.send_message(
                "This server is not whitelisted for general commands.",
                ephemeral=True
            )
            return False
            
        return True
    
    @app_commands.command(name="toggleheadpats", description="Turn on/off headpats in this server")
    async def toggle_headpats(self, interaction: discord.Interaction):
        """Toggle headpat functionality in this server."""
        # Only server admins or the bot owner can toggle
        if interaction.user.id != config.OWNER_ID and not interaction.user.guild_permissions.administrator:
            return await self.send_embed(
                interaction, 
                "Access Denied",
                "❌ You don't have permission to toggle this :<",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Load guild data
        guild_data = DataService.load_guild_data(interaction.guild.id)
        
        # Get or create headpats setting
        if "headpats_enabled" not in guild_data:
            guild_data["headpats_enabled"] = False
        
        # Toggle the setting
        guild_data["headpats_enabled"] = not guild_data["headpats_enabled"]
        
        # Save the updated setting
        DataService.save_guild_data(interaction.guild.id, guild_data)
        
        # Prepare response
        status = "enabled" if guild_data["headpats_enabled"] else "disabled"
        color = discord.Color.green() if guild_data["headpats_enabled"] else discord.Color.red()
        
        # Send response
        await self.send_embed(
            interaction,
            "Headpats Toggle",
            f"Head pats are now **{status}** in this server.",
            color
        )
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Respond with headpats image for configured users."""
        # Ignore bots, DMs, and empty content
        if (message.author.bot or 
            not message.guild or 
            not message.content):
            return
        
        # Get guild data
        guild_data = DataService.load_guild_data(message.guild.id)
        
        # Check if headpats are enabled for this guild
        if not guild_data.get("headpats_enabled", False):
            return
        
        # Check if user is in the target list
        if message.author.id not in config.TARGET_USER_ID:
            return
        
        # Send the headpat sticker
        image_url = "https://media.discordapp.net/stickers/1337638184040923148.webp"
        await message.reply(image_url)