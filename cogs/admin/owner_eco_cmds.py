"""
Owner economy commands implementation.
Provides commands for managing the economy system.
"""
import discord
import time
from discord import app_commands
from discord.ext import commands
import config
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ..cog_base import BotCog

@CommandRegistry.register_cog("admin")
class OwnerEconomyCommands(BotCog):
    """Owner-only commands for managing economy data."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.add_medals, self.remove_medals, self.ecoterminal]
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user has permission to use the command."""
        if interaction.user.id != config.OWNER_ID:
            await interaction.response.send_message(
                "❌ who are you??? YOU AREN'T SENNA 🔪", 
                ephemeral=True
            )
            return False
        return True
    
    @app_commands.command(name="add_medals", description="[OWNER] Add medals to a user's balance.")
    @app_commands.describe(
        target="The user to add medals to",
        amount="Amount of medals to add",
        account="Where to add the medals (pockets or savings)"
    )
    @app_commands.choices(
        account=[
            app_commands.Choice(name="Pockets", value="pockets"),
            app_commands.Choice(name="Savings", value="savings")
        ]
    )
    async def add_medals(self, interaction: discord.Interaction, target: discord.Member, amount: int, account: str):
        """Add medals to a user's balance."""
        if amount <= 0:
            return await self.send_embed(
                interaction, "Error",
                f"Amount must be positive. Use /remove_medals to remove medals.",
                discord.Color.red(), ephemeral=True
            )
        
        # Get user data
        user_data = DataService.get_user_data(interaction.guild.id, target.id, target.display_name)
        
        # Add medals to the appropriate account
        if account == "pockets":
            user_data["pockets"] = user_data.get("pockets", 0) + amount
            account_name = "pockets"
            new_balance = user_data["pockets"]
        else:  # savings
            user_data["savings"] = user_data.get("savings", 0) + amount
            account_name = "savings"
            new_balance = user_data["savings"]
        
        # Save the updated data
        guild_data = DataService.load_guild_data(interaction.guild.id)
        guild_data[str(target.id)] = user_data
        DataService.save_guild_data(interaction.guild.id, guild_data)
        
        await self.send_embed(
            interaction, "Medals Added",
            f"Added **{amount}** medals to {target.mention}'s {account_name}.\nNew balance: **{new_balance}** medals.",
            discord.Color.green(), ephemeral=True
        )
    
    @app_commands.command(name="remove_medals", description="[OWNER] Remove medals from a user's balance.")
    @app_commands.describe(
        target="The user to remove medals from",
        amount="Amount of medals to remove",
        account="Where to remove the medals from (pockets or savings)"
    )
    @app_commands.choices(
        account=[
            app_commands.Choice(name="Pockets", value="pockets"),
            app_commands.Choice(name="Savings", value="savings"),
            app_commands.Choice(name="Both (Pockets first)", value="both")
        ]
    )
    async def remove_medals(self, interaction: discord.Interaction, target: discord.Member, amount: int, account: str):
        """Remove medals from a user's balance."""
        if amount <= 0:
            return await self.send_embed(
                interaction, "Error",
                f"Amount must be positive.",
                discord.Color.red(), ephemeral=True
            )
        
        # Get user data
        user_data = DataService.get_user_data(interaction.guild.id, target.id, target.display_name)
        guild_data = DataService.load_guild_data(interaction.guild.id)
        
        if account == "pockets":
            current_pockets = user_data.get("pockets", 0)
            user_data["pockets"] = current_pockets - amount
            new_balance = user_data["pockets"]
            message = f"Removed **{amount}** medals from {target.mention}'s pockets.\nNew pocket balance: **{new_balance}** medals."
            
        elif account == "savings":
            current_savings = user_data.get("savings", 0)
            user_data["savings"] = current_savings - amount
            new_balance = user_data["savings"]
            message = f"Removed **{amount}** medals from {target.mention}'s savings.\nNew savings balance: **{new_balance}** medals."
            
        else:  # both
            current_pockets = user_data.get("pockets", 0)
            current_savings = user_data.get("savings", 0)
            
            # First take from pockets
            if current_pockets >= amount:
                user_data["pockets"] = current_pockets - amount
                new_pockets = user_data["pockets"]
                new_savings = current_savings
                message = f"Removed **{amount}** medals from {target.mention}'s pockets.\nNew pocket balance: **{new_pockets}** medals.\nSavings balance: **{new_savings}** medals."
            else:
                # Take whatever we can from pockets
                pockets_contribution = current_pockets
                savings_needed = amount - pockets_contribution
                
                # Take the rest from savings
                user_data["pockets"] = 0
                user_data["savings"] = current_savings - savings_needed
                
                new_pockets = user_data["pockets"]
                new_savings = user_data["savings"]
                
                message = f"Removed **{pockets_contribution}** medals from {target.mention}'s pockets and **{savings_needed}** medals from savings.\nNew pocket balance: **{new_pockets}** medals.\nNew savings balance: **{new_savings}** medals."
        
        # Save the updated data
        guild_data[str(target.id)] = user_data
        DataService.save_guild_data(interaction.guild.id, guild_data)
        
        await self.send_embed(
            interaction, "Medals Removed",
            message,
            discord.Color.orange(), ephemeral=True
        )
    
    @app_commands.command(name="ecoterminal", description="[OWNER] View and manipulate user's economy data.")
    @app_commands.describe(target="The user to view or modify")
    async def ecoterminal(self, interaction: discord.Interaction, target: discord.Member):
        """View and manage a user's economy data through an interactive UI."""
        # Get user data
        user_data = DataService.get_user_data(interaction.guild.id, target.id, target.display_name)
        
        # Create initial view
        view = EcoTerminalMainView(self, target, interaction.guild.id)
        
        # Create embed
        embed = self.create_status_embed(target, user_data)
        
        # Send initial message
        await interaction.response.send_message(embed=embed, view=view)
    
    def create_status_embed(self, target, user_data):
        """Create an embed with user's economy status."""
        pockets = user_data.get("pockets", 0)
        savings = user_data.get("savings", 0)
        injuries = user_data.get("injuries", 0)
        injured = user_data.get("injured", False)
        
        # Format injury status
        injury_status = "Healthy"
        if injured and injuries > 0:
            # Import at function level to avoid circular imports
            try:
                from cogs.economy.status.injury_system import get_injury_tier
                injury_tier = get_injury_tier(injuries)
                injury_status = injury_tier["name"]
            except ImportError:
                # Fallback if module not available
                if injuries >= 4:
                    injury_status = "Critical Condition"
                elif injuries >= 3:
                    injury_status = "Needs Surgery"
                elif injuries >= 2:
                    injury_status = "Moderate Injury"
                elif injuries >= 1:
                    injury_status = "Light Injury"
        
        # Format prison status
        prison_status = "Not in prison"
        if user_data.get("prison"):
            prison_tier = user_data["prison"].get("tier", "Unknown")
            release_time = user_data["prison"].get("release_time", 0)
            current_time = int(time.time())
            
            if release_time > current_time:
                time_left = release_time - current_time
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
                prison_status = f"In **{prison_tier}** for {hours}h {minutes}m"
            else:
                prison_status = f"In **{prison_tier}** (release time expired)"
        
        # Format cooldowns
        cooldowns = []
        current_time = int(time.time())
        for cmd, last_use in user_data.get("cooldowns", {}).items():
            if cmd and last_use:
                # Try to get cooldown from economy system
                try:
                    from cogs.economy.activities.work_cmds import DEFAULT_WORK_COOLDOWN
                    from cogs.economy.activities.crime_cmds import DEFAULT_CRIME_COOLDOWN
                    from cogs.economy.activities.rob_cmds import DEFAULT_ROB_COOLDOWN, ROB_VICTIM_COOLDOWN
                    from cogs.economy.games.roulette_game import DEFAULT_ROULETTE_COOLDOWN
                    from cogs.economy.prison.prison_system import ESCAPE_COOLDOWN, BREAKOUT_COOLDOWN
                    
                    cooldown_map = {
                        "work": DEFAULT_WORK_COOLDOWN,
                        "crime": DEFAULT_CRIME_COOLDOWN,
                        "rob": DEFAULT_ROB_COOLDOWN,
                        "roulette": DEFAULT_ROULETTE_COOLDOWN,
                        "escape": ESCAPE_COOLDOWN,
                        "breakout": BREAKOUT_COOLDOWN
                    }
                    
                    cooldown = cooldown_map.get(cmd, 0)
                except ImportError:
                    # Fallback cooldowns if modules not available
                    cooldown_map = {
                        "work": 60,      # 60 seconds
                        "crime": 75,     # 75 seconds
                        "rob": 300,      # 5 minutes
                        "roulette": 420, # 7 minutes
                        "escape": 120,   # 2 minutes
                        "breakout": 300  # 5 minutes
                    }
                    cooldown = cooldown_map.get(cmd, 0)
                
                elapsed = current_time - last_use
                if elapsed < cooldown:
                    remaining = cooldown - elapsed
                    minutes = remaining // 60
                    seconds = remaining % 60
                    cooldowns.append(f"**{cmd}**: {minutes}m {seconds}s")
        
        # Create embed
        embed = discord.Embed(
            title=f"Economy Status for {target.display_name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Balance", value=f"Pockets: **{pockets}** Medals\nSavings: **{savings}** Medals", inline=False)
        embed.add_field(name="Injury Status", value=f"**{injury_status}** (Level: {injuries})", inline=False)
        embed.add_field(name="Prison Status", value=prison_status, inline=False)
        
        # Add last robbed info if available
        if "last_robbed" in user_data and user_data["last_robbed"] > 0:
            last_robbed = user_data["last_robbed"]
            try:
                from cogs.economy.activities.rob_cmds import ROB_VICTIM_COOLDOWN
                remaining = (last_robbed + ROB_VICTIM_COOLDOWN) - current_time
                if remaining > 0:
                    minutes = remaining // 60
                    seconds = remaining % 60
                    rob_status = f"Cannot be robbed for {minutes}m {seconds}s"
                    embed.add_field(name="Rob Victim Status", value=rob_status, inline=False)
            except ImportError:
                # Skip this field if module is not available
                pass
        
        if cooldowns:
            embed.add_field(name="Active Cooldowns", value="\n".join(cooldowns), inline=False)
        else:
            embed.add_field(name="Active Cooldowns", value="No active cooldowns", inline=False)
        
        return embed


# Main view with category buttons
class EcoTerminalMainView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
    
    @discord.ui.button(label="Manage Injuries", style=discord.ButtonStyle.primary)
    async def injuries_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create injuries view
        view = InjuriesView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        embed.title = f"Injury Management for {self.target.display_name}"
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Manage Prison", style=discord.ButtonStyle.primary)
    async def prison_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create prison view
        view = PrisonView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        embed.title = f"Prison Management for {self.target.display_name}"
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Manage Cooldowns", style=discord.ButtonStyle.primary)
    async def cooldowns_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create cooldowns view
        view = CooldownsView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        embed.title = f"Cooldown Management for {self.target.display_name}"
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)


# Injuries management view
class InjuriesView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
    
    @discord.ui.button(label="Heal Injury", style=discord.ButtonStyle.success)
    async def heal_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Heal injuries - load and modify data directly
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key in guild_data:
            guild_data[user_key]["injuries"] = 0
            guild_data[user_key]["injured"] = False
            DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Injury Healed",
            description=f"All injuries have been healed for {self.target.mention}.",
            color=discord.Color.green()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Add Injury", style=discord.ButtonStyle.danger)
    async def add_injury_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Create add injury view
        view = AddInjuryView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = discord.Embed(
            title=f"Add Injury to {self.target.display_name}",
            description="Select the injury level to add:",
            color=discord.Color.orange()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create main view
        view = EcoTerminalMainView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)


# Add specific injury view
class AddInjuryView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
    
    @discord.ui.button(label="Light Injury", style=discord.ButtonStyle.secondary)
    async def light_injury_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Set injury to light (1)
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
            guild_data[user_key] = user_data
        
        guild_data[user_key]["injuries"] = 1
        guild_data[user_key]["injured"] = True
        DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Injury Added",
            description=f"Light Injury has been applied to {self.target.mention}.",
            color=discord.Color.orange()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Moderate Injury", style=discord.ButtonStyle.secondary)
    async def moderate_injury_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Set injury to moderate (2)
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
            guild_data[user_key] = user_data
        
        guild_data[user_key]["injuries"] = 2
        guild_data[user_key]["injured"] = True
        DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Injury Added",
            description=f"Moderate Injury has been applied to {self.target.mention}.",
            color=discord.Color.orange()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Needs Surgery", style=discord.ButtonStyle.danger)
    async def needs_surgery_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Set injury to needs surgery (3)
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
            guild_data[user_key] = user_data
        
        guild_data[user_key]["injuries"] = 3
        guild_data[user_key]["injured"] = True
        DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Injury Added",
            description=f"Needs Surgery condition has been applied to {self.target.mention}.",
            color=discord.Color.red()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Critical Condition", style=discord.ButtonStyle.danger)
    async def critical_condition_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Set injury to critical (4)
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
            guild_data[user_key] = user_data
        
        guild_data[user_key]["injuries"] = 4
        guild_data[user_key]["injured"] = True
        DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Injury Added",
            description=f"Critical Condition has been applied to {self.target.mention}.",
            color=discord.Color.dark_red()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Create injuries view
        view = InjuriesView(self.cog, self.target, self.guild_id)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        embed.title = f"Injury Management for {self.target.display_name}"
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)


# Prison management view
class PrisonView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
    
    @discord.ui.button(label="Free", style=discord.ButtonStyle.success)
    async def free_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Free from prison
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        was_in_prison = False
        prison_tier = None
        
        if user_key in guild_data and guild_data[user_key].get("prison"):
            was_in_prison = True
            prison_tier = guild_data[user_key]["prison"].get("tier", "Unknown")
            guild_data[user_key]["prison"] = None
            DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        if was_in_prison:
            embed = discord.Embed(
                title="Prison Release",
                description=f"{self.target.mention} has been freed from the {prison_tier}.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Prison Release",
                description=f"{self.target.mention} was not in prison.",
                color=discord.Color.green()
            )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Incarcerate", style=discord.ButtonStyle.danger)
    async def incarcerate_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Create incarcerate view
        view = IncarcerateView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = discord.Embed(
            title=f"Incarcerate {self.target.display_name}",
            description="Select the prison tier:",
            color=discord.Color.orange()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create main view
        view = EcoTerminalMainView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)


# Incarcerate view with prison tiers
class IncarcerateView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
        
        # Define prison tiers to show in the UI
        prison_tiers = [
            "Officer Group", "Old Guards", "Soldat Brigade", 
            "Lancer Legion", "Rook Division", "Mortician Wing", "Jaeger Camp"
        ]
        
        # Add prison tier buttons
        for tier_name in prison_tiers:
            button = discord.ui.Button(
                label=tier_name, 
                style=discord.ButtonStyle.secondary, 
                custom_id=f"prison_{tier_name}"
            )
            button.callback = self.prison_tier_callback
            self.add_item(button)
        
        # Add back button
        back_button = discord.ui.Button(
            label="Back", 
            style=discord.ButtonStyle.secondary, 
            custom_id="back"
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def prison_tier_callback(self, interaction):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get the selected tier from the button's custom_id
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("prison_"):
            tier_name = custom_id[7:]  # Remove "prison_" prefix
            
            # Incarcerate the user
            guild_data = DataService.load_guild_data(self.guild_id)
            user_key = str(self.target.id)
            
            if user_key not in guild_data:
                user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
                guild_data[user_key] = user_data
            
            # Try to get prison cooldown time from the system
            try:
                from cogs.economy.prison.prison_system import PRISON_COOLDOWN
                cooldown = PRISON_COOLDOWN
            except ImportError:
                cooldown = 3600  # Default to 1 hour if not available
            
            guild_data[user_key]["prison"] = {
                "tier": tier_name,
                "release_time": int(time.time()) + cooldown
            }
            DataService.save_guild_data(self.guild_id, guild_data)
            
            # Create confirmation embed
            embed = discord.Embed(
                title="Prison Sentence",
                description=f"{self.target.mention} has been sent to the {tier_name} for 1 hour.",
                color=discord.Color.orange()
            )
            
            # Update message
            await interaction.response.edit_message(embed=embed, view=None)
    
    async def back_callback(self, interaction):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Create prison view
        view = PrisonView(self.cog, self.target, self.guild_id)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        embed.title = f"Prison Management for {self.target.display_name}"
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)


# Cooldowns management view
class CooldownsView(discord.ui.View):
    def __init__(self, cog, target, guild_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.guild_id = guild_id
    
    @discord.ui.button(label="Refresh All", style=discord.ButtonStyle.success, row=0)
    async def refresh_all_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Reset all cooldowns
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key in guild_data:
            # Reset cooldowns dictionary
            guild_data[user_key]["cooldowns"] = {
                "work": 0, "crime": 0, "rob": 0, "roulette": 0, 
                "escape": 0, "breakout": 0
            }
            
            # Reset rob victim status
            guild_data[user_key]["last_robbed"] = 0
            
            DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Cooldowns Reset",
            description=f"All cooldowns have been reset for {self.target.mention}.",
            color=discord.Color.green()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Work", style=discord.ButtonStyle.secondary, row=1)
    async def work_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "work")
    
    @discord.ui.button(label="Crime", style=discord.ButtonStyle.secondary, row=1)
    async def crime_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "crime")
    
    @discord.ui.button(label="Rob", style=discord.ButtonStyle.secondary, row=1)
    async def rob_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "rob")
    
    @discord.ui.button(label="RobVictim", style=discord.ButtonStyle.secondary, row=2)
    async def rob_victim_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Reset last_robbed timestamp
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key in guild_data:
            guild_data[user_key]["last_robbed"] = 0
            DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Cooldown Reset",
            description=f"Rob victim cooldown has been reset for {self.target.mention}.",
            color=discord.Color.green()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Roulette", style=discord.ButtonStyle.secondary, row=2)
    async def roulette_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "roulette")
    
    @discord.ui.button(label="Escape", style=discord.ButtonStyle.secondary, row=2)
    async def escape_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "escape")
    
    @discord.ui.button(label="Breakout", style=discord.ButtonStyle.secondary, row=3)
    async def breakout_button(self, interaction, button):
        self._reset_specific_cooldown(interaction, "breakout")
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, row=3)
    async def back_button(self, interaction, button):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Get updated user data
        user_data = DataService.get_user_data(self.guild_id, self.target.id, self.target.display_name)
        
        # Create main view
        view = EcoTerminalMainView(self.cog, self.target, self.guild_id)
        
        # Create embed
        embed = self.cog.create_status_embed(self.target, user_data)
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=view)
    
    # Helper method for resetting specific cooldowns
    async def _reset_specific_cooldown(self, interaction, cooldown_type):
        # Check if the user is the owner
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ who are you??? YOU AREN'T SENNA 🔪", ephemeral=True)
        
        # Reset specific cooldown
        guild_data = DataService.load_guild_data(self.guild_id)
        user_key = str(self.target.id)
        
        if user_key in guild_data:
            if "cooldowns" not in guild_data[user_key]:
                guild_data[user_key]["cooldowns"] = {}
            
            guild_data[user_key]["cooldowns"][cooldown_type] = 0
            DataService.save_guild_data(self.guild_id, guild_data)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Cooldown Reset",
            description=f"{cooldown_type.capitalize()} cooldown has been reset for {self.target.mention}.",
            color=discord.Color.green()
        )
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=None)