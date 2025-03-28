"""
Leaderboard command implementation.
Provides the economy leaderboard command.
"""
import discord
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from ..economy_base import EconomyCog

@CommandRegistry.register_cog("economy")
class LeaderboardCog(EconomyCog):
    """Provides the leaderboard command for economy."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing LeaderboardCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.leaderboard]
    
    @app_commands.command(name="leaderboard", description="Show the server economy leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        """Show the server economy leaderboard."""
        # Load guild data
        data = DataService.load_guild_data(interaction.guild.id)
        
        if not data:
            return await self.send_embed(
                interaction, 
                "Leaderboard", 
                "No data available yet.",
                discord.Color.orange()
            )
        
        # Build leaderboard entries
        leaderboard = []
        for user_id, info in data.items():
            # Skip non-user entries 
            if not user_id.isdigit():
                continue
                
            # Calculate total balance
            total = info.get("pockets", 0) + info.get("savings", 0)
            username = info.get("username", "Unknown User")
            prison_status = info.get("prison", None)
            
            # Get injury status (simplified for now)
            if info.get("injured", False) and info.get("injuries", 0) > 0:
                injuries = info.get("injuries", 0)
                if injuries >= 4:
                    injury_tier = "Critical Condition"
                elif injuries >= 3:
                    injury_tier = "Needs Surgery"
                elif injuries >= 2:
                    injury_tier = "Moderate Injury"
                elif injuries >= 1:
                    injury_tier = "Light Injury"
                else:
                    injury_tier = "Healthy"
            else:
                injury_tier = "Healthy"
            
            leaderboard.append((user_id, total, username, prison_status, injury_tier))
        
        # Sort by total balance (highest to lowest)
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        
        # Format message
        message_lines = ["**Server Economy Leaderboard**\n"]
        
        for rank, (user_id, total, stored_name, prison_status, injury_tier) in enumerate(leaderboard, start=1):
            # Try to get member from guild
            member = interaction.guild.get_member(int(user_id))
            username = member.display_name if member else stored_name
            
            # Format prison status
            prison_text = ""
            if prison_status:
                prison_tier = prison_status.get("tier", "")
                prison_text = f" | 🔒 {prison_tier}"
            
            # Format injury status (only show if not healthy)
            injury_text = ""
            if injury_tier != "Healthy":
                injury_emoji = "🩹"  # Default injury emoji
                if injury_tier == "Moderate Injury":
                    injury_emoji = "🦼"
                elif injury_tier == "Needs Surgery":
                    injury_emoji = "🏥"
                elif injury_tier == "Critical Condition":
                    injury_emoji = "💀"
                injury_text = f" | {injury_emoji} {injury_tier}"
            
            # Add entry to leaderboard
            message_lines.append(f"**{rank}. {username}** {total} Medals{prison_text}{injury_text}")
        
        # Build final message
        message = "\n".join(message_lines)
        
        # Send leaderboard
        await self.send_embed(
            interaction, 
            "Leaderboard", 
            message, 
            discord.Color.gold(),
            ephemeral=True
        )