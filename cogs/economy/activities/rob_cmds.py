"""
Rob command implementation.
Provides the rob command for stealing Medals from other users.
"""
import discord
import random
import time
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from ..economy_base import EconomyCog
from ..status.injury_system import get_fail_rate, get_outcome_chance, DEATH_SAVINGS_PENALTY

# Default cooldowns and rob settings
DEFAULT_ROB_COOLDOWN = 300  # 300 seconds
ROB_VICTIM_COOLDOWN = 600   # 10 minutes protection for victims
ROB_MIN_AMOUNT = 15         # Minimum amount stolen on success

# Fine amounts
FINE_MIN = 5
FINE_MAX = 30

@CommandRegistry.register_cog("economy")
class RobCog(EconomyCog):
    """Provides the rob command for stealing Medals from other users."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing RobCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.rob]
    
    def handle_death(self, guild_id, user):
        """Handle death outcome - take medals from pockets and savings penalty."""
        # Get current values
        pockets_before = self.get_pockets(guild_id, user)
        savings = self.get_savings(guild_id, user)
        savings_penalty = int(savings * DEATH_SAVINGS_PENALTY)
        
        # Update balances
        self.update_pockets(guild_id, user, -pockets_before)  # Clear pockets
        
        # Apply savings penalty if possible
        if savings <= 0 or savings_penalty <= 0:
            # Can't pay savings penalty, send to prison instead
            prison_tier = "Officer Group"  # Default tier
            # Set prison status
            user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
            user_data["prison"] = {
                "tier": prison_tier,
                "release_time": int(time.time()) + 3600  # 1 hour
            }
            guild_data = DataService.load_guild_data(guild_id)
            guild_data[str(user.id)] = user_data
            DataService.save_guild_data(guild_id, guild_data)
            
            return pockets_before, 0, prison_tier
        else:
            # Normal death with savings penalty
            self.update_savings(guild_id, user, -savings_penalty)
            return pockets_before, savings_penalty, None
    
    def check_last_robbed(self, guild_id, user):
        """Check if a user was recently robbed and is protected."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        last_robbed = user_data.get("last_robbed", 0)
        current_time = int(time.time())
        elapsed = current_time - last_robbed
        
        if elapsed >= ROB_VICTIM_COOLDOWN:
            return True, 0
        
        return False, ROB_VICTIM_COOLDOWN - elapsed
    
    def set_last_robbed(self, guild_id, user):
        """Mark a user as recently robbed to provide protection."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        user_data["last_robbed"] = int(time.time())
        guild_data = DataService.load_guild_data(guild_id)
        guild_data[str(user.id)] = user_data
        DataService.save_guild_data(guild_id, guild_data)
    
    @app_commands.command(name="rob", description="Attempt to rob another member.")
    @app_commands.describe(target="The player you want to rob")
    async def rob(self, interaction: discord.Interaction, target: discord.Member):
        """Rob another member to steal their Medals."""
        # Check if trying to rob self
        if target.id == interaction.user.id:
            return await self.send_embed(
                interaction, 
                "Error",
                "Why are you trying to rob yourself???",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
            
        # Check if target was recently robbed
        can_be_robbed, remaining = self.check_last_robbed(interaction.guild.id, target)
        if not can_be_robbed:
            minutes, seconds = divmod(remaining, 60)
            cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            return await self.send_embed(
                interaction, 
                "You're an Asshole :<",
                f"**STOP {target.mention} IS ALREADY POOR D:**\n\n*Cannot be robbed again for another:* ***{cooldown_text}***.",
                discord.Color.orange(), 
                ephemeral=True
            )
        
        # Check cooldown using unified handler
        if not await self.handle_cooldown(interaction, "rob", DEFAULT_ROB_COOLDOWN):
            return
        
        # Get fail rate from injury system
        fail_rate = get_fail_rate(interaction.guild.id, interaction.user, "rob")
        
        # Roll for success/failure
        if random.randint(1, 100) <= fail_rate:
            # Rob failed - determine outcome
            
            # Calculate adjusted probabilities using injury system
            death_chance = get_outcome_chance("death", interaction.guild.id, interaction.user)
            prison_chance = get_outcome_chance("prison", interaction.guild.id, interaction.user)
            
            # Calculate remaining percentage for injury
            injury_chance = max(0, 100 - death_chance - prison_chance)
            
            # Roll for outcome
            outcome_roll = random.randint(1, 100)
            
            if outcome_roll <= death_chance:
                # Death outcome
                pockets_before, savings_penalty, prison_tier = self.handle_death(
                    interaction.guild.id, 
                    interaction.user
                )
                
                if prison_tier:
                    # Couldn't pay reaper's tax, sent to prison instead
                    prison_msg = self.get_response("prison")
                    
                    return await self.send_embed(
                        interaction, 
                        "Robbery Failed - Reaper's Tax Imprisonment!",
                        f"**You had no money to pay the reaper's tax, so you were sent to prison instead.**\n\n{prison_msg}",
                        discord.Color.dark_orange(),
                        extra_mentions=[target]
                    )
                else:
                    # Normal death with savings penalty
                    death_msg = self.get_response("rob_death", amount=pockets_before, target=target.mention)
                    
                    return await self.send_embed(
                        interaction, 
                        "Robbery Failed - Death!",
                        f"{death_msg}\n\n**{savings_penalty} Medals ({int(DEATH_SAVINGS_PENALTY*100)}% of your savings) have been taken to pay the reaper's tax**",
                        discord.Color.dark_red(),
                        extra_mentions=[target]
                    )
                    
            elif outcome_roll <= (death_chance + injury_chance):
                # Injury outcome
                fine_amount = random.randint(FINE_MIN, FINE_MAX)
                self.update_pockets(interaction.guild.id, interaction.user, -fine_amount)
                
                # Add an injury using injury system
                from ..status.injury_system import add_injury, get_injury_status
                add_injury(interaction.guild.id, interaction.user)
                injury_status = get_injury_status(interaction.guild.id, interaction.user)
                
                return await self.send_embed(
                    interaction, 
                    f"Robbery Failed - {injury_status['tier']}!",
                    f"{self.get_response('rob_injury', amount=fine_amount, target=target.mention)}\n\nYour condition: **{injury_status['tier']}**\n*You can walk it off :3*",
                    discord.Color.red(),
                    extra_mentions=[target]
                )
            else:
                # Prison outcome
                prison_tier = "Soldat Brigade"  # Default tier
                
                # Set prison status
                user_data = DataService.get_user_data(
                    interaction.guild.id, 
                    interaction.user.id, 
                    interaction.user.display_name
                )
                
                user_data["prison"] = {
                    "tier": prison_tier,
                    "release_time": int(time.time()) + 3600  # 1 hour
                }
                
                guild_data = DataService.load_guild_data(interaction.guild.id)
                guild_data[str(interaction.user.id)] = user_data
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                prison_msg = self.get_response("prison")
                
                return await self.send_embed(
                    interaction, 
                    "Robbery Failed - Prison!",
                    prison_msg,
                    discord.Color.dark_orange(),
                    extra_mentions=[target]
                )
        else:
            # Rob succeeded - check target's pockets
            target_pockets = self.get_pockets(interaction.guild.id, target)
            
            if target_pockets <= 5:
                # Target has almost nothing, not worth stealing
                return await self.send_embed(
                    interaction, 
                    "Robbery Attempt",
                    f"{target.mention} barely had anything to steal!",
                    discord.Color.orange(),
                    extra_mentions=[target]
                )
            
            # Calculate stolen amount with a minimum guarantee
            stolen = max(
                ROB_MIN_AMOUNT,
                random.randint(int(target_pockets * 0.6), int(target_pockets * 0.8))
            )
            
            # If the target has less than the minimum, take everything
            if target_pockets < ROB_MIN_AMOUNT:
                stolen = target_pockets
            
            # Update balances
            self.update_pockets(interaction.guild.id, interaction.user, stolen)
            self.update_pockets(interaction.guild.id, target, -stolen)
            
            # Set last robbed timestamp for the target
            self.set_last_robbed(interaction.guild.id, target)
            
            # Send success message
            success_msg = self.get_response("rob_success", target=target.mention, amount=stolen)
            await self.send_embed(
                interaction, 
                "Robbery Success", 
                success_msg, 
                discord.Color.green(),
                extra_mentions=[target]
            )