"""
Escape command implementation.
Provides the escape command for attempting to escape from prison.
"""
import discord
import random
import time
import asyncio
from discord import app_commands
from discord.ext import commands
from typing import List, Dict, Any, Tuple, Optional
from athena.cmd_registry import CommandRegistry
from athena.debug_tools import DebugTools
from athena.data_service import DataService
from athena.error_handler import command_error_handler

debug = DebugTools.get_debugger("escape_cmds")

# Death penalty for failed escapes (savings percentage)
DEATH_SAVINGS_PENALTY = 0.25  # 25% of savings

@CommandRegistry.register_cog("economy")
class EscapeCommands(commands.Cog):
    """Provides commands for escaping from prison."""
    
    def __init__(self, bot):
        self.bot = bot
        self.debug = DebugTools.get_debugger("escape_commands")
        self.debug.log("Initializing EscapeCommands")
        
        # Import inside method to avoid circular imports
        from ..economy_base import EconomyCog
        self.cog_base = EconomyCog(bot)
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.escape]
    
    def handle_death(self, guild_id: int, user: discord.Member) -> Tuple[int, int, Optional[str]]:
        """Handle death outcome from escape failures."""
        # Get current values
        pockets_before = self.cog_base.get_pockets(guild_id, user)
        savings = self.cog_base.get_savings(guild_id, user)
        savings_penalty = int(savings * DEATH_SAVINGS_PENALTY)
        
        # If user has very little savings or can't pay reaper's tax, send to prison instead
        if savings < 25 or savings <= 0 or savings_penalty <= 0:
            # Import at function level to avoid circular imports
            try:
                from .prison_system import send_to_prison, PRISON_COOLDOWN, select_prison_tier
                
                # Roll for prison tier
                tier = select_prison_tier()
                
                # Send to prison
                send_to_prison(guild_id, str(user.id), tier[0], PRISON_COOLDOWN)
                
                return pockets_before, 0, tier[0]  # Return prison tier as third value
            except ImportError as e:
                self.debug.log(f"Import error in handle_death: {e}")
                # Fallback if imports fail
                guild_data = DataService.load_guild_data(guild_id)
                user_key = str(user.id)
                
                if user_key not in guild_data:
                    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
                    guild_data[user_key] = user_data
                
                # Set default prison with one hour duration
                guild_data[user_key]["prison"] = {
                    "tier": "Officer Group",
                    "release_time": int(time.time()) + 3600
                }
                DataService.save_guild_data(guild_id, guild_data)
                
                return pockets_before, 0, "Officer Group"  # Return default tier
        else:
            # Normal case: take pocket money and savings penalty
            self.cog_base.update_pockets(guild_id, user, -pockets_before)
            self.cog_base.update_savings(guild_id, user, -savings_penalty)
            
            # Clear prison and injuries
            guild_data = DataService.load_guild_data(guild_id)
            user_key = str(user.id)
            
            if user_key in guild_data:
                guild_data[user_key]["prison"] = None
                guild_data[user_key]["injuries"] = 0
                guild_data[user_key]["injured"] = False
                DataService.save_guild_data(guild_id, guild_data)
            
            return pockets_before, savings_penalty, None  # No prison
    
    @app_commands.command(name="escape", description="Attempt to escape from prison.")
    @command_error_handler
    async def escape(self, interaction: discord.Interaction):
        """Attempt to escape from prison."""
        try:
            # Import at function level to avoid circular imports
            from .prison_system import ESCAPE_COOLDOWN, format_time, get_escape_chance_modifier, PRISON_TIERS
            
            # Check cooldown first
            can_escape, remaining = self.cog_base.check_cooldown(
                interaction.guild.id, 
                interaction.user, 
                "escape", 
                ESCAPE_COOLDOWN
            )
            
            if not can_escape:
                minutes, seconds = divmod(remaining, 60)
                cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
                return await self.cog_base.send_embed(
                    interaction, 
                    "Escape Cooldown",
                    f"You're too tired to try to escape. Rest for **{cooldown_text}**.",
                    discord.Color.orange(), 
                    ephemeral=True
                )
            
            # Check if user is in prison
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            
            # Get user data (auto-creates if not exists)
            user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
            prison = user_data.get("prison")
            
            if not prison:
                return await self.cog_base.send_embed(
                    interaction, 
                    "Escape",
                    "Escape? From WHAT??? You're not in prison!",
                    discord.Color.orange(), 
                    ephemeral=True
                )
            
            # Set cooldown at the beginning to prevent escape spam
            self.cog_base.set_cooldown(interaction.guild.id, interaction.user, "escape")
            
            # Get prison tier details
            tier_key = prison.get("tier")
            tier = next((t for t in PRISON_TIERS if t[0] == tier_key), None)
            
            if not tier:
                return await self.cog_base.send_embed(
                    interaction, 
                    "Escape",
                    "Your prison data is corrupted. Please contact an administrator.",
                    discord.Color.red(), 
                    ephemeral=True
                )
            
            # Special case for Jaeger Camp - use the button game
            if tier_key == "Jaeger Camp":
                embed = discord.Embed(
                    title="The Four Boxes",
                    description=f"The Jaegers have caught you trying to escape.\n\nThey drag you into a room with many more of them with malice in their eyes and sadist smiles across their face.\n\n**They present to you 4 different colored boxes:**\n\n1 box contains a **Playing Card**\n1 box contains a **Broken Watch**\n1 box contains stolen **Medical Supplies**\n1 box contains a **Knife**\n\n***Choose wisely...***",
                    color=discord.Color.orange()
                )
                
                # Import at function level
                from .ui_components.jaeger_components import EscapeJaegerView
                view = EscapeJaegerView(self.cog_base, interaction, interaction.user.id)
                await interaction.response.send_message(
                    content=f"{interaction.user.mention}",
                    embed=embed,
                    view=view
                )
                return
            
            # Normal escape logic for other prisons
            # Get base escape chance from tier
            base_escape_chance = tier[2]
            
            # Modify escape chance based on injury tier
            escape_chance_mod = get_escape_chance_modifier(interaction.guild.id, interaction.user.id)
            escape_chance = base_escape_chance + escape_chance_mod
            
            # Ensure escape chance doesn't go below 5%
            escape_chance = max(5, escape_chance)
            
            # Roll for escape
            roll = random.randint(1, 100)
            
            if roll <= escape_chance:
                # Successful escape
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                # Get appropriate response for this prison tier
                success_key = f"escape_success_{tier_key.lower().replace(' ', '_')}"
                try:
                    from athena.response_manager import ResponseManager
                    success_msg = ResponseManager.get_response(success_key)
                except:
                    # Fallback to generic message
                    success_msg = f"You successfully escaped from the {tier_key}!"
                
                return await self.cog_base.send_embed(
                    interaction, 
                    "Escape Successful!",
                    success_msg,
                    discord.Color.green()
                )
            else:
                # Failed escape - handle penalties based on tier
                try:
                    from athena.response_manager import ResponseManager
                    fail_key = f"escape_failure_{tier_key.lower().replace(' ', '_')}"
                    fail_msg = ResponseManager.get_response(fail_key)
                except:
                    # Fallback to generic message
                    fail_msg = f"Your escape attempt from the {tier_key} has failed!"
                    
                # Apply specific prison tier penalties
                penalty_text = ""
                
                # Officer Group: No change
                if tier_key == "Officer Group":
                    pass
                
                # Old Guards: -5 Medals from savings
                elif tier_key == "Old Guards":
                    self.cog_base.update_savings(interaction.guild.id, interaction.user, -5)
                    penalty_text = "\n\n**5 Medals** were deducted from your savings."
                
                # Soldat Brigade: -10 Medals from savings
                elif tier_key == "Soldat Brigade":
                    self.cog_base.update_savings(interaction.guild.id, interaction.user, -10)
                    penalty_text = "\n\n**10 Medals** were deducted from your savings."
                
                # Lancer Legion: Gain injury and -15 Medals from savings
                elif tier_key == "Lancer Legion":
                    self.cog_base.update_savings(interaction.guild.id, interaction.user, -15)
                    
                    # Only add injury if not already at Critical Condition
                    from ..status.injury_system import get_injury_status, add_injury
                    injury_status = get_injury_status(interaction.guild.id, interaction.user)
                    if injury_status["tier"] != "Critical Condition":
                        add_injury(interaction.guild.id, interaction.user)
                        
                    new_status = get_injury_status(interaction.guild.id, interaction.user)
                    penalty_text = f"\n\n**15 Medals** were deducted from your savings and your condition is now **{new_status['tier']}**."
                
                # Rook Division: Increase time by 15 minutes and gain injury
                elif tier_key == "Rook Division":
                    # Extend prison time
                    guild_data = DataService.load_guild_data(interaction.guild.id)
                    user_key = str(interaction.user.id)
                    
                    if user_key in guild_data and guild_data[user_key].get("prison"):
                        # Import at function level
                        from .prison_system import PRISON_COOLDOWN
                        prison_time = guild_data[user_key]["prison"].get("release_time", int(time.time()) + PRISON_COOLDOWN)
                        prison_time += (15 * 60)  # Add 15 minutes
                        guild_data[user_key]["prison"]["release_time"] = prison_time
                        DataService.save_guild_data(interaction.guild.id, guild_data)
                    
                    # Add injury if not already at Critical Condition
                    from ..status.injury_system import get_injury_status, add_injury
                    injury_status = get_injury_status(interaction.guild.id, interaction.user)
                    if injury_status["tier"] != "Critical Condition":
                        add_injury(interaction.guild.id, interaction.user)
                        
                    new_status = get_injury_status(interaction.guild.id, interaction.user)
                    penalty_text = f"\n\nYour sentence was extended by **15 minutes** and your condition is now **{new_status['tier']}**."
                
                # Mortician Wing: Special injury handling
                elif tier_key == "Mortician Wing":
                    from ..status.injury_system import get_injury_status
                    injury_status = get_injury_status(interaction.guild.id, interaction.user)
                    
                    if injury_status["tier"] == "Critical Condition":
                        # Already at max injury - just take medals
                        self.cog_base.update_savings(interaction.guild.id, interaction.user, -20)
                        penalty_text = f"\n\nThe Morts have taken all the willpower out of you and took **20 Medals** from your savings instead."
                    elif injury_status["tier"] == "Needs Surgery":
                        # Move to Critical Condition
                        guild_data = DataService.load_guild_data(interaction.guild.id)
                        user_key = str(interaction.user.id)
                        
                        if user_key in guild_data:
                            guild_data[user_key]["injuries"] = 4  # Set to Critical Condition
                            guild_data[user_key]["injured"] = True
                            DataService.save_guild_data(interaction.guild.id, guild_data)
                            
                        penalty_text = f"\n\nYour condition has worsened to **Critical Condition**"
                    else:
                        # Set to Needs Surgery
                        guild_data = DataService.load_guild_data(interaction.guild.id)
                        user_key = str(interaction.user.id)
                        
                        if user_key in guild_data:
                            guild_data[user_key]["injuries"] = 3  # Set to Needs Surgery
                            guild_data[user_key]["injured"] = True
                            DataService.save_guild_data(interaction.guild.id, guild_data)
                            
                        penalty_text = f"\n\nYour condition has worsened to **Needs Surgery**"
                
                # Return failure message with penalty
                return await self.cog_base.send_embed(
                    interaction, 
                    "Escape Failed!",
                    f"{fail_msg}{penalty_text}",
                    discord.Color.red()
                )
                
        except Exception as e:
            self.debug.log(f"Error in escape command: {e}")
            await self.cog_base.send_embed(
                interaction,
                "Error",
                "An error occurred while processing your escape attempt.",
                discord.Color.red(),
                ephemeral=True
            )