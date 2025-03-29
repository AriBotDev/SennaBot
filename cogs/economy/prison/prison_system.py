"""
Prison system implementation.
Provides the core functionality for the prison system.
"""
import discord
import random
import time
import asyncio
from discord.ext import commands
from typing import Tuple, Optional
from athena.cmd_registry import CommandRegistry
from athena.debug_tools import DebugTools
from athena.data_service import DataService

# Setup debugger
debug = DebugTools.get_debugger("prison_system")

# Prison tier definitions
PRISON_TIERS = [
    ("Officer Group", 35, 75),    # Name, weight, escape chance
    ("Old Guards", 20, 65),
    ("Soldat Brigade", 15, 50),
    ("Lancer Legion", 10, 40),
    ("Rook Division", 10, 40),
    ("Mortician Wing", 5, 25),
    ("Jaeger Camp", 5, 10)
]

# Prison cooldown time in seconds
PRISON_COOLDOWN = 3600  # 1 hour
ESCAPE_COOLDOWN = 120   # 2 minutes
BREAKOUT_COOLDOWN = 300 # 5 minutes

def select_prison_tier() -> Tuple[str, int, int]:
    """
    Select a random prison tier based on weights.
    Returns the tier details: (name, weight, escape_chance)
    """
    weights = [tier[1] for tier in PRISON_TIERS]
    total_weight = sum(weights)
    
    # Generate a random number within the total weight
    roll = random.randint(1, total_weight)
    
    # Determine which tier was selected
    running_total = 0
    for tier in PRISON_TIERS:
        running_total += tier[1]
        if roll <= running_total:
            return tier
    
    # Fallback to the last tier
    return PRISON_TIERS[-1]

def format_time(seconds: int) -> str:
    """Format seconds into a human-readable string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def get_escape_chance_modifier(guild_id: int, user_id: int) -> int:
    """
    Get escape chance modifier based on user's injury status.
    Returns a negative value (penalty) to be added to the base escape chance.
    """
    # Load user data
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data:
        return 0
    
    user_data = guild_data[user_key]
    injuries = user_data.get("injuries", 0)
    injury_status = user_data.get("injured", False)
    
    if not injury_status or injuries <= 0:
        return 0
    
    # Apply penalties based on injury level
    if injuries >= 4:  # Critical Condition
        return -25
    elif injuries >= 3:  # Needs Surgery
        return -15
    elif injuries >= 2:  # Moderate Injury
        return -5
    elif injuries >= 1:  # Light Injury
        return -3
    
    return 0

def is_in_prison(guild_id: int, user_id: int) -> bool:
    """Check if a user is currently in prison."""
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data:
        return False
    
    prison_data = guild_data[user_key].get("prison")
    if not prison_data:
        return False
    
    # Check if prison time is up
    current_time = int(time.time())
    release_time = prison_data.get("release_time", 0)
    
    if current_time >= release_time:
        # Auto-release user
        guild_data[user_key]["prison"] = None
        DataService.save_guild_data(guild_id, guild_data)
        return False
    
    return True

def get_prison_tier(guild_id: int, user_id: int) -> Optional[str]:
    """
    Get a user's prison tier if they are in prison.
    Returns None if the user is not in prison.
    """
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data:
        return None
    
    prison_data = guild_data[user_key].get("prison")
    if not prison_data:
        return None
    
    # Check if prison time is up
    current_time = int(time.time())
    release_time = prison_data.get("release_time", 0)
    
    if current_time >= release_time:
        # Auto-release user
        guild_data[user_key]["prison"] = None
        DataService.save_guild_data(guild_id, guild_data)
        return None
    
    return prison_data.get("tier")

def get_release_time(guild_id: int, user_id: int) -> Optional[int]:
    """
    Get a user's prison release time if they are in prison.
    Returns None if the user is not in prison.
    """
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data:
        return None
    
    prison_data = guild_data[user_key].get("prison")
    if not prison_data:
        return None
    
    return prison_data.get("release_time", 0)

def send_to_prison(guild_id: int, user_id: str, tier: str = None, duration: int = PRISON_COOLDOWN) -> None:
    """
    Send a user to prison with the specified tier and duration.
    If tier is not specified, a random tier will be selected.
    """
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data:
        # Get or create user data
        user_data = DataService.get_user_data(guild_id, int(user_id))
        guild_data[user_key] = user_data
    
    # Select a tier if not specified
    if not tier:
        tier_info = select_prison_tier()
        tier = tier_info[0]
    
    # Set prison data
    guild_data[user_key]["prison"] = {
        "tier": tier,
        "release_time": int(time.time()) + duration
    }
    
    DataService.save_guild_data(guild_id, guild_data)

def release_from_prison(guild_id: int, user_id: int) -> bool:
    """
    Release a user from prison with proper error handling.
    Returns True if the user was in prison and was released, False otherwise.
    """
    try:
        guild_data = DataService.load_guild_data(guild_id)
        user_key = str(user_id)
        
        if user_key not in guild_data or not guild_data[user_key].get("prison"):
            return False
        
        guild_data[user_key]["prison"] = None
        DataService.save_guild_data(guild_id, guild_data)
        debug.log(f"Released user {user_id} from prison in guild {guild_id}")
        return True
    except Exception as e:
        debug = DebugTools.get_debugger("prison_system")
        debug.log(f"Error releasing from prison: {e}")
        return False

def extend_prison_time(guild_id: int, user_id: int, additional_time: int) -> bool:
    """
    Extend a user's prison time by the specified amount (in seconds).
    Returns True if the user was in prison and time was extended, False otherwise.
    """
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user_id)
    
    if user_key not in guild_data or not guild_data[user_key].get("prison"):
        return False
    
    # Get current release time
    release_time = guild_data[user_key]["prison"].get("release_time", int(time.time()))
    
    # Extend the time
    guild_data[user_key]["prison"]["release_time"] = release_time + additional_time
    
    DataService.save_guild_data(guild_id, guild_data)
    return True

@CommandRegistry.register_cog("economy")
class PrisonSystem(commands.Cog):
    """Core prison system functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        # Import inside method to avoid circular imports
        from ..economy_base import EconomyCog
        self.cog_base = EconomyCog(bot)
        self.debug = DebugTools.get_debugger("prison_system")
        self.debug.log("Initializing PrisonSystem")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return []  # This cog has no direct app commands
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Process any prisoners who should be released when the bot starts."""
        self.debug.log("Checking for expired prison sentences")
        
        bot_guilds = [guild.id for guild in self.bot.guilds]
        released_count = 0
        
        for guild_id in bot_guilds:
            guild_data = DataService.load_guild_data(guild_id)
            current_time = int(time.time())
            guild_updated = False
            
            for user_id, user_data in guild_data.items():
                # Skip non-user entries
                if not user_id.isdigit():
                    continue
                
                prison = user_data.get("prison")
                if not prison:
                    continue
                
                release_time = prison.get("release_time", 0)
                
                # Check if prison time is up
                if current_time >= release_time:
                    self.debug.log(f"Auto-releasing user {user_id} from {prison.get('tier')} prison")
                    guild_data[user_id]["prison"] = None
                    guild_updated = True
                    released_count += 1
            
            if guild_updated:
                DataService.save_guild_data(guild_id, guild_data)
        
        self.debug.log(f"Released {released_count} prisoners on startup")