"""
Base cog class for all bot cogs.
Provides shared functionality for cogs.
"""
import discord
from discord.ext import commands
from athena.debug_tools import DebugTools
from athena.logging_service import LoggingService
from athena.response_manager import ResponseManager

class BotCog(commands.Cog):
    """Base cog for all bot cogs."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = LoggingService.get_logger(self.__class__.__name__)
        self.debug = DebugTools.get_debugger(self.__class__.__name__)
    
    async def send_embed(self, ctx, title: str, description: str, color=discord.Color.blurple(), 
                        ephemeral: bool = False, extra_mentions: list = None):
        """
        Create and send an embed message.
        Works with both interactions and context.
        """
        extra_mentions = extra_mentions or []
        embed = discord.Embed(title=title, description=description, color=color)
        
        # Handle both Interaction and Context
        if isinstance(ctx, discord.Interaction):
            mention_text = ctx.user.mention
        else:
            mention_text = ctx.author.mention
            
        # Add extra mentions
        if extra_mentions:
            mention_text += " " + " ".join(user.mention for user in extra_mentions)
        
        # Send the message
        try:
            if isinstance(ctx, discord.Interaction):
                if not ctx.response.is_done():
                    await ctx.response.send_message(
                        content=mention_text,
                        embed=embed,
                        ephemeral=ephemeral,
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )
                else:
                    await ctx.followup.send(
                        content=mention_text,
                        embed=embed,
                        ephemeral=ephemeral,
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )
            else:
                await ctx.reply(
                    content=mention_text,
                    embed=embed,
                    mention_author=False,
                    allowed_mentions=discord.AllowedMentions(users=True)
                )
            return True
        except Exception as e:
            self.debug.log(f"Error sending embed: {e}")
            return False
    
    def get_response(self, key: str, **kwargs) -> str:
        """
        Get a themed response for a key.
        """
        return ResponseManager.get_response(key, **kwargs)
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """
        Default permission check for app commands.
        Override in subclasses for category-specific checks.
        """
        # Check for DMs - most commands don't work in DMs
        return await self.check_permissions(interaction)
    
    async def check_permissions(self, interaction: discord.Interaction, category=None):
        """
        Standard permission check method for all cogs.
        Returns True if user has permission, False otherwise.
        """
        # Check for DMs
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return False
        
        # If category is specified, check guild permission
        if category:
            from athena.perm_manager import PermissionManager
            if not PermissionManager.get_guild_permission(interaction.guild.id, category):
                await interaction.response.send_message(
                    f"This server is not whitelisted for {category} commands.",
                    ephemeral=True
                )
                return False
        
        return True
