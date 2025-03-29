"""
Base class for economy cogs.
Provides common functionality for all economy cogs.
"""
import discord
import time
from discord.ext import commands
from athena.data_service import DataService
from ..cog_base import BotCog

class EconomyCog(BotCog):
    """Base cog for all economy-related commands."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """Check economy permissions and other prerequisites."""
        # First run the base check
        if not await super().cog_app_command_check(interaction):
            return False
            
        # Then check economy permissions
        from athena.perm_manager import PermissionManager
        if not PermissionManager.get_guild_permission(interaction.guild.id, "economy"):
            await interaction.response.send_message(
                "This server is not whitelisted for economy commands.",
                ephemeral=True
            )
            return False
            
        return True
    
    async def check_prison_status(self, ctx):
        """Check if user is in prison."""
        user_data = DataService.get_user_data(ctx.guild.id, ctx.user.id, ctx.user.display_name)
        if user_data.get("prison"):
            await self.send_embed(
                ctx, 
                "Prison", 
                "You are in prison and cannot use this command.", 
                discord.Color.red(), 
                ephemeral=True
            )
            return False
        return True
    
    async def check_balance_challenge(self, ctx):
        """Check if user is in a balance challenge."""
        try:
            # Import here to avoid circular imports
            from .games.balance_challenge import is_in_challenge
            
            # Check if user is in an active challenge
            if is_in_challenge(ctx.user.id):
                await self.send_embed(
                    ctx, 
                    "Balance Challenge", 
                    "You are currently in a balance challenge and cannot use this command.", 
                    discord.Color.red(), 
                    ephemeral=True
                )
                return False
        except ImportError:
            # If balance_challenge module isn't loaded yet, allow the command
            self.debug.log("Balance challenge module not loaded yet, allowing command")
        return True
    
    def get_pockets(self, guild_id, user):
        """Get the amount of Medals in a user's pockets."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        return user_data.get("pockets", 0)
    
    def get_savings(self, guild_id, user):
        """Get the amount of Medals in a user's savings."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        return user_data.get("savings", 0)
    
    def update_pockets(self, guild_id, user, amount):
        """Update a user's pocket balance with thread safety."""
        with DataService.get_guild_lock(guild_id):
            user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
            current_balance = user_data.get("pockets", 0)
            
            # For withdrawals, ensure sufficient funds if we don't allow negative balances
            allow_negative_pockets = True  # Set to True if we want to allow negative balances
            if amount < 0 and abs(amount) > current_balance and not allow_negative_pockets:
                self.debug.log(f"Attempted to withdraw {abs(amount)} from pockets with balance {current_balance}")
                return current_balance  # Return unchanged balance
                
            user_data["pockets"] = current_balance + amount
            guild_data = DataService.load_guild_data(guild_id)
            guild_data[str(user.id)] = user_data
            DataService.save_guild_data(guild_id, guild_data)
            return user_data["pockets"]

    def update_savings(self, guild_id, user, amount):
        """Update a user's savings balance with thread safety."""
        with DataService.get_guild_lock(guild_id):
            user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
            current_balance = user_data.get("savings", 0)
            
            # For withdrawals, ensure sufficient funds if we don't allow negative balances
            allow_negative_savings = True  # Set to True if we want to allow negative balances
            if amount < 0 and abs(amount) > current_balance and not allow_negative_savings:
                self.debug.log(f"Attempted to withdraw {abs(amount)} from savings with balance {current_balance}")
                return current_balance  # Return unchanged balance
                
            user_data["savings"] = current_balance + amount
            guild_data = DataService.load_guild_data(guild_id)
            guild_data[str(user.id)] = user_data
            DataService.save_guild_data(guild_id, guild_data)
            return user_data["savings"]
    
    def set_cooldown(self, guild_id, user, command):
        """Set a cooldown for a command."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        if "cooldowns" not in user_data:
            user_data["cooldowns"] = {}
        user_data["cooldowns"][command] = int(time.time())
        guild_data = DataService.load_guild_data(guild_id)
        guild_data[str(user.id)] = user_data
        DataService.save_guild_data(guild_id, guild_data)
    
    def check_cooldown(self, guild_id, user, command, cooldown_time):
        """Check if a command is on cooldown."""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        cooldowns = user_data.get("cooldowns", {})
        last_used = cooldowns.get(command, 0)
        current_time = int(time.time())
        elapsed = current_time - last_used
        
        if elapsed >= cooldown_time:
            return True, 0
        
        return False, cooldown_time - elapsed
        
    async def handle_cooldown(self, interaction, command_name, cooldown_time, ephemeral=True):
        """
        Unified cooldown handler that checks and sets cooldowns.
        Returns True if command can proceed, False if on cooldown.
        """
        try:
            # Check cooldown
            can_use, remaining = self.check_cooldown(
                interaction.guild.id, 
                interaction.user, 
                command_name, 
                cooldown_time
            )
            
            if not can_use:
                minutes, seconds = divmod(remaining, 60)
                cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
                await self.send_embed(
                    interaction, 
                    "Cooldown",
                    f"You cannot use this command for another **{cooldown_text}**.",
                    discord.Color.orange(), 
                    ephemeral=ephemeral
                )
                return False
            
            # If not on cooldown, set a new cooldown and return True
            self.set_cooldown(interaction.guild.id, interaction.user, command_name)
            return True
        except Exception as e:
            self.debug.log(f"Error in handle_cooldown: {e}")
            # Try to send a simpler error message if the fancy one fails
            try:
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
            except:
                pass
            return False