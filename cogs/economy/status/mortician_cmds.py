"""
Mortician commands implementation.
Provides the see_mortician command for healing injuries.
"""
import discord
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from athena.error_handler import command_error_handler
from ..economy_base import EconomyCog

# Setup debugger
debug = DebugTools.get_debugger("mortician_cmds")

@CommandRegistry.register_cog("economy")
class MorticianCommands(EconomyCog):
    """Provides commands for visiting the mortician to heal injuries."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing MorticianCommands")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.see_mortician]
    
    @app_commands.command(name="see_mortician", description="Visit the Mortician's Wing to heal your injuries.")
    @command_error_handler
    async def see_mortician(self, interaction: discord.Interaction):
        """Visit the mortician to heal injuries."""
        # Check if user is in prison
        guild_data = DataService.load_guild_data(interaction.guild.id)
        user_key = str(interaction.user.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
        else:
            user_data = guild_data[user_key]
                
        prison = user_data.get("prison")
        if prison and prison.get("tier") == "Mortician Wing":
            return await self.send_embed(
                interaction, "Mortician's Hell",
                "No matter how much you beg...the morts would rather see you in pain...",
                discord.Color.red(), ephemeral=False
            )
        elif prison and prison.get("tier") == "Jaeger Camp":
            return await self.send_embed(
                interaction, "Jaeger's Resolve",
                "Jaeger's don't need Morts. So neither do you. Suffer in silence...",
                discord.Color.red(), ephemeral=False
            )
                
        # Get injury status
        from .injury_system import get_injury_status
        injury_status = get_injury_status(interaction.guild.id, interaction.user)
        injuries = injury_status["injuries"]
        
        if injuries <= 0:
            return await self.send_embed(
                interaction, "Mortician's Wing",
                "You are not injured. Did you just come here to steal my stims???",
                discord.Color.orange(), ephemeral=True
            )
                
        heal_cost = injury_status["heal_cost"]
        
        # Check if user has enough funds
        pockets = self.get_pockets(interaction.guild.id, interaction.user)
        savings = self.get_savings(interaction.guild.id, interaction.user)
        total_funds = pockets + savings
        
        if total_funds < heal_cost:
            return await self.send_embed(
                interaction, "Mortician's Wing",
                f"You need **{heal_cost}** Medals to heal your {injury_status['tier']}. You only have **{total_funds}** Medals total.",
                discord.Color.red(), ephemeral=True
            )
        
        # Handle negative pocket balance
        if pockets < 0:
            return await self.send_embed(
                interaction, "Error",
                "You have a negative pocket balance. Resolve your debt before healing.",
                discord.Color.red(), ephemeral=True
            )
                
        # Take money from pockets first, then savings if needed
        if pockets >= heal_cost:
            self.update_pockets(interaction.guild.id, interaction.user, -heal_cost)
        else:
            remainder = heal_cost - pockets
            self.update_pockets(interaction.guild.id, interaction.user, -pockets)
            self.update_savings(interaction.guild.id, interaction.user, -remainder)
                
        # Heal all injuries
        from .injury_system import heal_injuries
        heal_injuries(interaction.guild.id, interaction.user)
        
        await self.send_embed(
            interaction, "Mortician's Wing",
            f"The Mortician tended to your {injury_status['tier']} for **{heal_cost}** Medals <3",
            discord.Color.green(), ephemeral=False
        )