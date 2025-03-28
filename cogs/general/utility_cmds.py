"""
Utility commands implementation.
Provides general utility commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.debug_tools import DebugTools
from ..cog_base import BotCog

@CommandRegistry.register_cog("general")
class UtilityCommands(BotCog):
    """Provides utility commands."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.gdtrello]
    
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
    
    @app_commands.command(name="gdtrello", description="Reply with the GD Trello link")
    async def gdtrello(self, interaction: discord.Interaction):
        """Provide the Grave/Digger Trello board link."""
        trello_link = "https://trello.com/b/PtRtvsCj/grave-digger-real-official-trello"
        
        await self.send_embed(
            interaction,
            "Grave/Digger Trello",
            f"I found the Grave/Digger Trello board! :D \n[Click Here]({trello_link})",
            discord.Color.blue(),
            ephemeral=True
        )