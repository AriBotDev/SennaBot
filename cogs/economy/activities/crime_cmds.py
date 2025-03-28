"""
Crime command implementation.
Provides the crime command for earning Medals with risk.
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
DEFAULT_CRIME_COOLDOWN = 75  # 75 seconds
CRIME_PAYOUT_MIN = 15
CRIME_PAYOUT_MAX = 35
CRIME_FAIL_RATE = 51  # 51% chance to fail
CRITICAL_SUCCESS_CHANCE = 2  # 2% chance
CRITICAL_MULTIPLIER_MIN = 3  # 3x multiplier
CRITICAL_MULTIPLIER_MAX = 5  # 5x multiplier

# Failure outcome probabilities
CRIME_DEATH_CHANCE = 15    # 15% chance for death on failure
CRIME_INJURY_CHANCE = 65   # 65% chance for injury on failure
# Remaining 20% is prison

# Fine amounts
FINE_MIN = 5
FINE_MAX = 30

# Death penalty
DEATH_SAVINGS_PENALTY = 0.10  # 10% of savings

@CommandRegistry.register_cog("economy")
class CrimeCog(EconomyCog):
    """Provides the crime command for earning Medals with risk."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing CrimeCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.crime]
    
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
    
    @app_commands.command(name="crime", description="Commit a crime for Medals (risk involved).")
    async def crime(self, interaction: discord.Interaction):
        """Commit a crime to earn Medals with risk."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
            
        # Check cooldown
        can_crime, remaining = self.check_cooldown(
            interaction.guild.id, 
            interaction.user, 
            "crime", 
            DEFAULT_CRIME_COOLDOWN
        )
        
        if not can_crime:
            minutes, seconds = divmod(remaining, 60)
            cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            return await self.send_embed(
                interaction, 
                "Cooldown",
                f"You cannot commit a crime for another **{cooldown_text}**.",
                discord.Color.orange(), 
                ephemeral=True
            )
        
        # Get fail rate (will be modified by injury status later)
        fail_rate = CRIME_FAIL_RATE
        
        # Roll for success/failure
        if random.randint(1, 100) <= fail_rate:
            # Crime failed - determine outcome
            
            # Temporary injury and prison modifiers (will be replaced by actual system)
            death_chance_mod = 0
            prison_chance_mod = 0
            
            # Calculate adjusted probabilities
            modified_death_chance = CRIME_DEATH_CHANCE + death_chance_mod
            modified_prison_chance = (100 - CRIME_DEATH_CHANCE - CRIME_INJURY_CHANCE) + prison_chance_mod
            
            # Calculate remaining percentage for injury
            modified_injury_chance = max(0, 100 - modified_death_chance - modified_prison_chance)
            
            # Roll for outcome
            outcome_roll = random.randint(1, 100)
            
            # Set cooldown regardless of outcome
            self.set_cooldown(interaction.guild.id, interaction.user, "crime")
            
            if outcome_roll <= modified_death_chance:
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
                        "Crime Failed - Reaper's Tax Imprisonment!",
                        f"**You had no money to pay the reaper's tax, so you were sent to prison instead.**\n\n{prison_msg}",
                        discord.Color.dark_orange()
                    )
                else:
                    # Normal death with savings penalty
                    death_msg = self.get_response("death", amount=pockets_before)
                    
                    return await self.send_embed(
                        interaction, 
                        "Crime Failed - Death!",
                        f"{death_msg}\n\n**{savings_penalty} Medals ({int(DEATH_SAVINGS_PENALTY*100)}% of your savings) have been taken to pay the reaper's tax**",
                        discord.Color.dark_red()
                    )
                    
            elif outcome_roll <= (modified_death_chance + modified_injury_chance):
                # Injury outcome
                fine_amount = random.randint(FINE_MIN, FINE_MAX)
                self.update_pockets(interaction.guild.id, interaction.user, -fine_amount)
                
                # Add an injury
                # This will be implemented when we add the injury system
                # For now, just use a placeholder injury tier
                injury_tier = "Light Injury"
                
                return await self.send_embed(
                    interaction, 
                    f"Crime Failed - {injury_tier}!",
                    f"{self.get_response('injury', amount=fine_amount)}\n\nYour condition: **{injury_tier}**\n*You can walk it off :3*",
                    discord.Color.red()
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
                    "Crime Failed - Prison!",
                    prison_msg,
                    discord.Color.dark_orange()
                )
        else:
            # Crime succeeded
            
            # Base reward
            reward = random.randint(CRIME_PAYOUT_MIN, CRIME_PAYOUT_MAX)
            
            # Apply earning multiplier (will be implemented with injury system)
            earning_multiplier = 1.0
            reward = int(reward * earning_multiplier)
            
            # Get bot settings (or use defaults if not available)
            critical_chance = DataService.get_bot_setting("critical_success_chance", CRITICAL_SUCCESS_CHANCE)
            min_multiplier = DataService.get_bot_setting("critical_multiplier_min", CRITICAL_MULTIPLIER_MIN)
            max_multiplier = DataService.get_bot_setting("critical_multiplier_max", CRITICAL_MULTIPLIER_MAX)
            
            # Check for critical success
            is_critical = random.randint(1, 100) <= critical_chance
            
            if is_critical:
                # Apply random multiplier
                multiplier = random.randint(min_multiplier, max_multiplier)
                original_reward = reward
                reward = reward * multiplier
                
                # Get a rare success message
                success_msg = self.get_response(
                    "crime_rare_success", 
                    amount=reward, 
                    multiplier=multiplier, 
                    original=original_reward
                )
                title = f"Crime - **{multiplier}x** CRITICAL SUCCESS!"
                color = discord.Color.gold()
            else:
                # Regular success
                success_msg = self.get_response("crime_success", amount=reward)
                title = "Crime Success"
                color = discord.Color.green()
            
            # Update user's balance
            self.update_pockets(interaction.guild.id, interaction.user, reward)
            
            # Set cooldown
            self.set_cooldown(interaction.guild.id, interaction.user, "crime")
            
            # Send response
            await self.send_embed(interaction, title, success_msg, color)