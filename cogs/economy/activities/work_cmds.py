"""
Work command implementation.
Provides the work command for earning Medals.
"""
import discord
import random
import time
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from ..economy_base import EconomyCog

# Default cooldowns and payouts
DEFAULT_WORK_COOLDOWN = 60  # 60 seconds
WORK_PAYOUT_MIN = 4
WORK_PAYOUT_MAX = 12
CRITICAL_SUCCESS_CHANCE = 2  # 2% chance
CRITICAL_MULTIPLIER_MIN = 3  # 3x multiplier
CRITICAL_MULTIPLIER_MAX = 5  # 5x multiplier

@CommandRegistry.register_cog("economy")
class WorkCog(EconomyCog):
    """Provides the work command for earning Medals."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing WorkCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.work]
    
    @app_commands.command(name="work", description="Work to earn Medals.")
    async def work(self, interaction: discord.Interaction):
        """Work to earn Medals."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
            
        # Check cooldown
        can_work, remaining = self.check_cooldown(
            interaction.guild.id, 
            interaction.user, 
            "work", 
            DEFAULT_WORK_COOLDOWN
        )
        
        if not can_work:
            minutes, seconds = divmod(remaining, 60)
            cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            return await self.send_embed(
                interaction, 
                "Cooldown",
                f"You cannot work for another **{cooldown_text}**.",
                discord.Color.orange(), 
                ephemeral=True
            )
        
        # Get bot settings (or use defaults if not available)
        critical_chance = DataService.get_bot_setting("critical_success_chance", CRITICAL_SUCCESS_CHANCE)
        min_multiplier = DataService.get_bot_setting("critical_multiplier_min", CRITICAL_MULTIPLIER_MIN)
        max_multiplier = DataService.get_bot_setting("critical_multiplier_max", CRITICAL_MULTIPLIER_MAX)
        
        # Base wage
        wage = random.randint(WORK_PAYOUT_MIN, WORK_PAYOUT_MAX)
        
        # Apply earning multiplier based on injury status (to be implemented)
        earning_multiplier = 1.0  # Default, will be replaced with actual implementation
        wage = int(wage * earning_multiplier)
        
        # Check for critical success
        is_critical = random.randint(1, 100) <= critical_chance
        
        if is_critical:
            # Apply random multiplier between min and max
            multiplier = random.randint(min_multiplier, max_multiplier)
            original_wage = wage
            wage = wage * multiplier
            
            # Get a rare success message
            message = self.get_response("work_rare_success", amount=wage, multiplier=multiplier, original=original_wage)
            title = f"Work - **{multiplier}x** CRITICAL SUCCESS!"
            color = discord.Color.gold()
        else:
            # Regular success
            message = self.get_response("work", amount=wage)
            title = "Work"
            color = discord.Color.green()
        
        # Add injury status to message if injured
        # This will be implemented when we add the injury system
        
        # Update user's balance
        self.update_pockets(interaction.guild.id, interaction.user, wage)
        
        # Set cooldown
        self.set_cooldown(interaction.guild.id, interaction.user, "work")
        
        # Send response
        await self.send_embed(interaction, title, message, color)