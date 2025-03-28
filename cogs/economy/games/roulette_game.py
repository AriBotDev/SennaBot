"""
Roulette game implementation.
Provides the roulette command for gambling.
"""
import discord
import random
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from ..economy_base import EconomyCog

# Default cooldown
DEFAULT_ROULETTE_COOLDOWN = 420  # 7 minutes

@CommandRegistry.register_cog("economy")
class RouletteCog(EconomyCog):
    """Provides the roulette command for gambling Medals."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing RouletteCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.roulette]
    
    @app_commands.command(name="roulette", description="Play roulette: bet on purple, yellow, or green!")
    @app_commands.describe(bet="How many Medals you want to bet", choice="Pick a color")
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Purple", value="purple"),
            app_commands.Choice(name="Yellow", value="yellow"),
            app_commands.Choice(name="Green", value="green")
        ]
    )
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: str):
        """Play roulette to gamble Medals."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
        
        # Check cooldown
        can_play, remaining = self.check_cooldown(
            interaction.guild.id, 
            interaction.user, 
            "roulette", 
            DEFAULT_ROULETTE_COOLDOWN
        )
        
        if not can_play:
            minutes, seconds = divmod(remaining, 60)
            cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            return await self.send_embed(
                interaction, 
                "Cooldown",
                f"You cannot play roulette for another **{cooldown_text}**.",
                discord.Color.orange(), 
                ephemeral=True
            )
        
        # Validate bet
        if bet <= 0:
            return await self.send_embed(
                interaction, 
                "Error", 
                "What's the point of betting nothing???", 
                discord.Color.red(), 
                ephemeral=True
            )
            
        # Check if player has enough Medals
        pockets = self.get_pockets(interaction.guild.id, interaction.user)
        if bet > pockets:
            return await self.send_embed(
                interaction, 
                "Error", 
                "HA HA YOU DON'T HAVE ENOUGH MONEY NOOB!", 
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Deduct bet amount
        self.update_pockets(interaction.guild.id, interaction.user, -bet)
        
        # Send initial message
        ephemeral_text = f"You bet {bet} on **{choice}...**"
        await self.send_embed(
            interaction, 
            "Roulette", 
            ephemeral_text, 
            discord.Color.blurple()
        )
        
        # Determine outcome
        # Purple: 18/37 chance, Yellow: 18/37 chance, Green: 1/37 chance
        outcome = random.choices(
            ["purple", "yellow", "green"], 
            weights=[18, 18, 1], 
            k=1
        )[0]
        
        # Calculate result
        if outcome == choice:
            # Player wins
            multiplier = 2 if outcome in ["purple", "yellow"] else 14
            payout = bet * multiplier
            
            # Update balance
            self.update_pockets(interaction.guild.id, interaction.user, payout)
            
            # Send result message
            await self.send_embed(
                interaction, 
                "Roulette Win",
                f"The ball landed on **{outcome} (x{multiplier})**!\n\nYou won **{payout} Medals :D**",
                discord.Color.green()
            )
        else:
            # Player loses
            await self.send_embed(
                interaction, 
                "Roulette L",
                f"The ball landed on **{outcome}**.\n\nYou lost your bet of **{bet} Medals D:**",
                discord.Color.red()
            )
        
        # Set cooldown
        self.set_cooldown(interaction.guild.id, interaction.user, "roulette")