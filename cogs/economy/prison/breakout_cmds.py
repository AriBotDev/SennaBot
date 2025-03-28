"""
Breakout command implementation.
Provides the breakout command for freeing other users from prison.
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
from athena.error_handler import ErrorHandler
from ..economy_base import EconomyCog
from .prison_system import (
    select_prison_tier, format_time, get_escape_chance_modifier, 
    is_in_prison, get_prison_tier, release_from_prison,
    PRISON_TIERS, PRISON_COOLDOWN, ESCAPE_COOLDOWN, BREAKOUT_COOLDOWN
)
from .ui_components.breakout_components import (
    OfficerGroupBreakoutView, OldGuardsBreakoutView, SoldatBrigadeBreakoutView,
    LancerLegionBreakoutView, RookDivisionBreakoutView, MorticianWingBreakoutView,
    JaegerPathBreakoutView
)
from ..status.injury_system import add_injury, get_injury_status

debug = DebugTools.get_debugger("breakout_cmds")

@CommandRegistry.register_cog("economy")
class BreakoutCommands(EconomyCog):
    """Provides commands for breaking other users out of prison."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug = DebugTools.get_debugger("breakout_commands")
        self.debug.log("Initializing BreakoutCommands")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.breakout]
    
    @app_commands.command(name="breakout", description="Attempt to break another player out of prison.")
    @app_commands.describe(target="The player you want to break out of prison")
    async def breakout(self, interaction: discord.Interaction, target: discord.Member):
        """Attempt to break another player out of prison."""
        # Check if initiator is in prison
        if not await self.prison_check(interaction):
            return
            
        # Check if initiator is in a balance challenge
        if not await self.challenge_check(interaction):
            return
        
        # Check if target is valid
        if target.id == interaction.user.id:
            return await self.send_embed(
                interaction, 
                "Error",
                "Use `/escape` to escape yourself from prison... Don't act stupid!",
                discord.Color.red(), 
                ephemeral=True
            )
        
        if target.bot:
            return await self.send_embed(
                interaction, 
                "Error",
                "You can't break out a bot. They've probably already escaped on their own anyway.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check if target is in prison
        guild_data = DataService.load_guild_data(interaction.guild.id)
        target_key = str(target.id)
        
        if target_key not in guild_data:
            user_data = DataService.get_user_data(interaction.guild.id, target.id, target.display_name)
            guild_data[target_key] = user_data
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
        target_data = guild_data[target_key]
        target_prison = target_data.get("prison")
        
        if not target_prison:
            return await self.send_embed(
                interaction, 
                "Error",
                f"{target.display_name} is not in prison!",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check breakout cooldown
        self.check_cooldown(interaction.guild.id, interaction.user, "breakout", BREAKOUT_COOLDOWN)         
        can_breakout, remaining = self.check_cooldown(interaction.guild.id, interaction.user, "breakout", BREAKOUT_COOLDOWN)
                        
        if not can_breakout:
            return await self.send_embed(
                interaction, 
                "Breakout Cooldown",
                f"You need to wait **{format_time(remaining)}** before attempting another breakout.",
                discord.Color.orange(), 
                ephemeral=True
            )
        
        # Set cooldown right away to prevent abuse
        self.set_cooldown(interaction.guild.id, interaction.user, "breakout")
        
        # Determine prison tier and launch appropriate minigame
        tier_key = target_prison.get("tier")
        
        # Create appropriate view based on prison tier
        if tier_key == "Officer Group":
            embed = discord.Embed(
                title="Officer Group Breakout",
                description="**Just walk through the door...**",
                color=discord.Color.blue()
            )
            view = OfficerGroupBreakoutView(self, interaction, target, target_prison)
            
        elif tier_key == "Old Guards":
            embed = discord.Embed(
                title="Old Guards Breakout",
                description="The guards are sleeping...\n\n**Steal the keys c:<**",
                color=discord.Color.blue()
            )
            view = OldGuardsBreakoutView(self, interaction, target, target_prison)
            
        elif tier_key == "Soldat Brigade":
            embed = discord.Embed(
                title="Soldat Brigade Breakout",
                description="It's teeming with Soldats patrolling around the prison...\n\n**Pick a door to enter through**",
                color=discord.Color.blue()
            )
            view = SoldatBrigadeBreakoutView(self, interaction, target, target_prison)
            
        elif tier_key == "Lancer Legion":
            embed = discord.Embed(
                title="Lancer Legion Breakout",
                description="You hear cheering down the hallways...\n\nThe Legion is hosting a feast tonight. **Pick a door to enter through. Do not pick the wrong one**",
                color=discord.Color.blue()
            )
            view = LancerLegionBreakoutView(self, interaction, target, target_prison)

        elif tier_key == "Rook Division":
            embed = discord.Embed(
                title="Rook Division Breakout",
                description="It'd be impossible to try to break into the Rook's domain by force.\n\nMaybe you can pick the locks instead...\n\n**Pick the correct order of pins to break in.**\n*Lockpick Durability: (4)*",
                color=discord.Color.blue()
            )
            view = RookDivisionBreakoutView(self, interaction, target, target_prison)
            
        elif tier_key == "Mortician Wing":
            embed = discord.Embed(
                title="Mortician Wing Breakout",
                description="You decided to disguise yourself as a Mort to gain entry into the prison.\n\nHowever, the authenticity of your disguise is quite...questionable...\nThe other Morts would like to test your pharmaceutical knowledge.\n\nIn front of you are **6 different colored vials of stims with covered labels**.\nIn russian roulette fashion, please pick a bottle to test on other prisoners until 1 remains.\n\nIf the **last bottle remaining is Amatoxin**, you will have succesfully fooled the Morts. Otherwise, **if you pick a bottle that ends up being Amatoxin**, it will be you who plays the fool...",
                color=discord.Color.blue()
            )
            view = MorticianWingBreakoutView(self, interaction, target, target_prison)
            
        elif tier_key == "Jaeger Camp":
            embed = discord.Embed(
                title="Jaeger Camp Breakout",
                description="Breaking into the Jaeger Camp will prove difficult.\n\nYou soon find yourself trapped in the middle of a cave system filled with Jaeger traps.\n\n**Traverse Carefully**\n*Succesfully traverse 8 paths before reaching Critical Condition*",
                color=discord.Color.blue()
            )
            view = JaegerPathBreakoutView(self, interaction, target, target_prison)
            
        else:
            return await self.send_embed(
                interaction, 
                "Error",
                "Unknown prison tier. Please contact Senna.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        await interaction.response.send_message(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=view
        )