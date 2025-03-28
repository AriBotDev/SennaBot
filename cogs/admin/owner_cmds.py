"""
Owner commands implementation.
Provides commands for managing bot configuration and whitelist.
"""
import discord
import sys
import importlib
from discord import app_commands
from discord.ext import commands
import config
from athena.cmd_registry import CommandRegistry
from athena.perm_manager import PermissionManager
from athena.debug_tools import DebugTools
from athena.data_service import DataService
from athena.error_handler import ErrorHandler
from ..cog_base import BotCog

@CommandRegistry.register_cog("admin")
class OwnerCommands(BotCog):
    """Owner-only slash commands for managing whitelists and more."""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.whitelist, self.whitelist_show, self.whitelist_update, self.reload_cogs]
    
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user has permission to use the command."""
        if interaction.user.id != config.OWNER_ID:
            await interaction.response.send_message(
                "❌ who are you??? YOU AREN'T SENNA 🔪", 
                ephemeral=True
            )
            return False
        return True
    
    @app_commands.command(name="whitelist", description="Manage a server's whitelist status for a given category.")
    @app_commands.describe(
        action="Specify 'add' or 'remove'",
        category="Whitelist category (e.g., economy). Defaults to 'general'.",
        guild_id="Target guild ID (defaults to the current guild)"
    )
    async def whitelist(self, interaction: discord.Interaction, action: str, category: str = "general", guild_id: str = None):
        """Manage server whitelist settings for command categories."""
        # Get target guild ID
        target_id = guild_id or str(interaction.guild.id)
        guild_name = interaction.guild.name if interaction.guild and str(interaction.guild.id) == target_id else None
        
        # Validate category
        if category not in PermissionManager.ALLOWED_CATEGORIES:
            return await self.send_embed(
                interaction,
                "Invalid Category",
                f"Category `{category}` is not valid. Allowed categories: {', '.join(PermissionManager.ALLOWED_CATEGORIES)}.",
                discord.Color.red(),
                ephemeral=True
            )
        
        # Process action
        if action.lower() == "add":
            success = PermissionManager.update_permission(target_id, category, True, guild_name)
            if success:
                embed = discord.Embed(
                    title="Whitelist Updated",
                    description=f"Server `{target_id}` has been whitelisted for **{category}**.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to update whitelist. Check logs for details.",
                    color=discord.Color.red()
                )
        elif action.lower() == "remove":
            success = PermissionManager.update_permission(target_id, category, False, guild_name)
            if success:
                embed = discord.Embed(
                    title="Whitelist Updated",
                    description=f"Server `{target_id}` has been removed from the **{category}** whitelist.",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to update whitelist. Check logs for details.",
                    color=discord.Color.red()
                )
        else:
            embed = discord.Embed(
                title="Invalid Action",
                description="Use `add` or `remove` as the action.",
                color=discord.Color.red()
            )
        
        # Send response before potentially longer reload operation
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Now reload commands to apply whitelist changes
        if action.lower() in ["add", "remove"] and success:
            await CommandRegistry.sync_all_guilds(self.bot)
    
    @app_commands.command(name="whitelist_show", description="Show the current whitelist status for all servers.")
    async def whitelist_show(self, interaction: discord.Interaction):
        """Show the current whitelist status for all servers."""
        # Load permissions
        permissions = PermissionManager.load_permissions()
        
        if not permissions:
            embed = discord.Embed(
                title="Whitelist", 
                description="No servers are currently whitelisted.",
                color=discord.Color.orange()
            )
        else:
            lines = []
            for gid, entry in permissions.items():
                server_name = entry.get("server_name", "Unknown")
                cats = [cat for cat in PermissionManager.ALLOWED_CATEGORIES if entry.get(cat, False)]
                cats_str = ", ".join(cats) if cats else "None"
                lines.append(f"`{gid}` - **{server_name}**: {cats_str}")
            
            desc = "\n".join(lines)
            embed = discord.Embed(
                title="Whitelist", 
                description=desc,
                color=discord.Color.gold()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="whitelist_update", description="Update whitelist entries to include new categories.")
    async def whitelist_update(self, interaction: discord.Interaction):
        """Update whitelist entries to include new categories."""
        # Load permissions
        permissions = PermissionManager.load_permissions(force_reload=True)
        updated = False
        
        for gid, entry in permissions.items():
            for cat in PermissionManager.ALLOWED_CATEGORIES:
                if cat not in entry:
                    # Force owner guild to be whitelisted for everything
                    if str(gid) == PermissionManager.OWNER_GUILD_ID:
                        entry[cat] = True
                    else:
                        entry[cat] = False
                    updated = True
        
        if updated:
            # Save updated permissions
            PermissionManager.save_permissions(permissions)
            embed = discord.Embed(
                title="Whitelist Updated", 
                description="Whitelist entries have been updated with new categories.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Whitelist Update", 
                description="No updates were necessary. All entries are up-to-date.",
                color=discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Reload commands if entries were updated
        if updated:
            await CommandRegistry.sync_all_guilds(self.bot)
    
    @app_commands.command(name="reload_cogs", description="Reload all bot cogs and update commands based on the whitelist.")
    async def reload_cogs(self, interaction: discord.Interaction):
        """Reload all bot cogs and update commands."""
        # Let user know operation is in progress
        embed = discord.Embed(
            title="Reload Cogs",
            description="Reloading cogs and syncing commands. Please wait...",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # Get the list of extensions to reload
        extensions = [
            "cogs.general.general_module",
            "cogs.admin.admin_module",
            "cogs.economy.economy_module"
        ]
        
        reloaded = []
        failed = []
        
        # First unload all cogs to clean slate
        for cog_name in list(self.bot.cogs.keys()):
            try:
                await self.bot.remove_cog(cog_name)
                self.debug.log(f"Removed cog {cog_name}")
            except Exception as e:
                self.debug.log(f"Error removing cog {cog_name}: {e}")
        
        # Clean up modules from sys.modules
        for name in list(sys.modules.keys()):
            if name.startswith('cogs.') and not name.endswith('__init__'):
                try:
                    del sys.modules[name]
                    self.debug.log(f"Removed module {name} from sys.modules")
                except KeyError:
                    pass
        
        # Now load extensions fresh
        for ext in extensions:
            try:
                await self.bot.load_extension(ext)
                reloaded.append(ext)
                self.debug.log(f"Successfully loaded extension {ext}")
            except Exception as e:
                failed.append(f"{ext}: {e}")
                self.debug.log(f"Failed to load extension {ext}: {e}")
        
        # Now call the centralized sync function
        await CommandRegistry.sync_all_guilds(self.bot)
        
        # Update with results
        desc = ""
        if reloaded:
            desc += "Reloaded extensions:\n" + "\n".join(reloaded)
        if failed:
            desc += "\n\nFailed to reload:\n" + "\n".join(failed)
        
        result_embed = discord.Embed(
            title="Reload Complete",
            description=desc or "No extensions to reload.",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=result_embed, ephemeral=False)