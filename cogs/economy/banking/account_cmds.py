"""
Account commands implementation.
Provides balance, deposit, and withdraw commands.
"""
import discord
import time
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from ..economy_base import EconomyCog

@CommandRegistry.register_cog("economy")
class AccountCog(EconomyCog):
    """Provides banking commands for managing Medals."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing AccountCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.balance, self.deposit, self.withdraw, self.donate]
    
    @app_commands.command(name="balance", description="Check your or another member's balance.")
    @app_commands.describe(member="The member whose balance to check")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        """Check your or another member's balance."""
        # Use caller if no member specified
        member = member or interaction.user
        
        # Get balances
        pockets = self.get_pockets(interaction.guild.id, member)
        savings = self.get_savings(interaction.guild.id, member)
        
        # Create description
        desc = (f"{member.mention}\n\n**{pockets}** Medals in pockets\n"
                f"**{savings}** Medals in savings")
                
        await self.send_embed(interaction, "Balance", desc, discord.Color.green())
    
    @app_commands.command(name="deposit", description="Deposit Medals into your savings.")
    @app_commands.describe(amount="Amount to deposit or 'all'")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        """Deposit Medals from pockets to savings."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
        
        # Check for negative pocket balance
        pockets = self.get_pockets(interaction.guild.id, interaction.user)
        if pockets < 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "You have a negative pocket balance. You cannot deposit until you resolve your debt.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Handle "all" amount
        if amount.lower() == "all":
            if pockets <= 0:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "What are you even trying to deposit?",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Deposit all pocket Medals
            self.update_pockets(interaction.guild.id, interaction.user, -pockets)
            self.update_savings(interaction.guild.id, interaction.user, pockets)
            
            await self.send_embed(
                interaction, 
                "Deposit All Successful",
                f"Deposited all **{pockets}** Medals from pockets to savings.",
                discord.Color.green()
            )
        else:
            # Handle numeric amount
            try:
                amount_val = int(amount)
            except ValueError:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "Please provide a valid number or 'all'",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Validate amount
            if amount_val <= 0:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "Are you trying to rob ME????",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            if amount_val > pockets:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "You don't have that much money in your pockets, silly.",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Perform deposit
            self.update_pockets(interaction.guild.id, interaction.user, -amount_val)
            self.update_savings(interaction.guild.id, interaction.user, amount_val)
            
            await self.send_embed(
                interaction, 
                "Deposit Successful",
                f"Deposited **{amount_val}** Medals from pockets to savings.",
                discord.Color.green()
            )
    
    @app_commands.command(name="withdraw", description="Withdraw Medals from your savings.")
    @app_commands.describe(amount="Amount to withdraw or 'all'")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        """Withdraw Medals from savings to pockets."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
        
        # Check for negative savings balance
        savings = self.get_savings(interaction.guild.id, interaction.user)
        if savings < 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "You have a negative savings balance. You cannot withdraw until you resolve your debt.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Handle "all" amount
        if amount.lower() == "all":
            if savings <= 0:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "U HAVE NO MONEY. GET OUT UR POOR",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Withdraw all savings
            self.update_savings(interaction.guild.id, interaction.user, -savings)
            self.update_pockets(interaction.guild.id, interaction.user, savings)
            
            await self.send_embed(
                interaction, 
                "Withdrawal All Successful",
                f"Withdrew all **{savings}** Medals from savings to pockets.",
                discord.Color.green()
            )
        else:
            # Handle numeric amount
            try:
                amount_val = int(amount)
            except ValueError:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "Please provide a valid number or 'all'.",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Validate amount
            if amount_val <= 0:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "Are you GIVING me money???",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            if amount_val > savings:
                return await self.send_embed(
                    interaction, 
                    "Error",
                    "You don't have that much money in your savings. Get a job, LOSER!!!",
                    discord.Color.red(), 
                    ephemeral=True
                )
                
            # Perform withdrawal
            self.update_savings(interaction.guild.id, interaction.user, -amount_val)
            self.update_pockets(interaction.guild.id, interaction.user, amount_val)
            
            await self.send_embed(
                interaction, 
                "Withdrawal Successful",
                f"Withdrew **{amount_val}** Medals from savings to pockets.",
                discord.Color.green()
            )
    
    @app_commands.command(name="donate", description="Donate Medals to another member.")
    @app_commands.describe(target="The member to donate to", amount="Amount to donate")
    async def donate(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        """Donate Medals to another member."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
        
        # Can't donate to self
        if target.id == interaction.user.id:
            return await self.send_embed(
                interaction, 
                "Error",
                "You cannot donate to yourself idiot...",
                discord.Color.red(), 
                ephemeral=True
            )
            
        # Validate amount
        if amount <= 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "Donation amount must be positive....",
                discord.Color.red(), 
                ephemeral=True
            )
            
        # Check if donor has enough funds
        donor_pockets = self.get_pockets(interaction.guild.id, interaction.user)
        donor_savings = self.get_savings(interaction.guild.id, interaction.user)
        total_donor_funds = donor_pockets + donor_savings
        
        if amount > total_donor_funds:
            return await self.send_embed(
                interaction, 
                "Error",
                "You don't have enough funds to donate that amount. It looks like YOU need a donation.",
                discord.Color.red(), 
                ephemeral=True
            )
            
        if donor_pockets < 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "Your pocket balance is negative; you cannot donate until you resolve your debt.",
                discord.Color.red(), 
                ephemeral=True
            )
            
        if donor_savings < 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "Your savings balance is negative; you cannot donate until you resolve your debt.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Process donation
        if donor_pockets >= amount:
            # Take entirely from pockets
            self.update_pockets(interaction.guild.id, interaction.user, -amount)
        else:
            # Take what's available from pockets, rest from savings
            remainder = amount - donor_pockets
            self.update_pockets(interaction.guild.id, interaction.user, -donor_pockets)
            self.update_savings(interaction.guild.id, interaction.user, -remainder)
        
        # Give to recipient's pockets
        self.update_pockets(interaction.guild.id, target, amount)
        
        # Send confirmation
        await self.send_embed(
            interaction, 
            "Donation Successful",
            f"{interaction.user.mention} donated **{amount}** Medals to {target.mention} <3",
            discord.Color.green(),
            extra_mentions=[target]
        )