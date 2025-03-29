"""
Injury system implementation.
Provides the status command and injury-related utilities.
"""
import discord
import datetime
import time
from discord import app_commands
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from athena.error_handler import command_error_handler

# Setup debugger
debug = DebugTools.get_debugger("injury_system")

# Injury tier definitions moved from economy_config.py to here
INJURY_TIERS = [
    {
        "name": "Light Injury", 
        "heal_cost": 10, 
        "threshold": 1,
        "effects": {
            "cooldown_multiplier": 1.2,  # 20% longer cooldowns
            "fail_rate_mod": 0,          # No additional fail rate
            "earning_penalty": 0,        # No earning penalty
            "death_chance_mod": 0,       # No death chance modifier
            "prison_chance_mod": 0,      # No prison chance modifier
            "guaranteed_fail": False     # Not guaranteed to fail
        }
    },
    {
        "name": "Moderate Injury", 
        "heal_cost": 15, 
        "threshold": 2,
        "effects": {
            "cooldown_multiplier": 1.2,  # 20% longer cooldowns
            "fail_rate_mod": 10,         # +10% fail rate
            "earning_penalty": 0,        # No earning penalty
            "death_chance_mod": 0,       # No death chance modifier
            "prison_chance_mod": 0,      # No prison chance modifier
            "guaranteed_fail": False     # Not guaranteed to fail
        }
    },
    {
        "name": "Needs Surgery", 
        "heal_cost": 30, 
        "threshold": 3,
        "effects": {
            "cooldown_multiplier": 1.2,  # 20% longer cooldowns
            "fail_rate_mod": 10,         # +10% fail rate
            "earning_penalty": 0.2,      # 20% earning penalty
            "death_chance_mod": 15,      # +15% death chance on failure
            "prison_chance_mod": 20,     # +20% prison chance on failure
            "guaranteed_fail": False     # Not guaranteed to fail
        }
    },
    {
        "name": "Critical Condition", 
        "heal_cost": 50, 
        "threshold": 4,
        "effects": {
            "cooldown_multiplier": 1.2,  # 20% longer cooldowns
            "fail_rate_mod": 25,         # High failure rate but not guaranteed
            "earning_penalty": 0.2,      # 20% earning penalty
            "death_chance_mod": 25,      # +25% death chance on failure
            "prison_chance_mod": 30,     # +30% prison chance on failure
            "guaranteed_fail": False     # Not guaranteed failure - slim chance to succeed
        }
    }
]

# Define base fail rates here to avoid circular imports
FAIL_RATES = {
    "crime": 51,
    "rob": 55
}

OUTCOME_CHANCES = {
    "death": 15,    # 15% chance for death on failure
    "injury": 65,   # 65% chance for injury on failure
    "prison": 20    # 20% chance for prison on failure (remainder)
}

DEATH_SAVINGS_PENALTY = 0.10

def get_injury_tier(injuries: int) -> dict:
    """Determine the injury tier based on the number of injuries"""
    for tier in reversed(INJURY_TIERS):
        if injuries >= tier["threshold"]:
            return tier
    return {"name": "Healthy", "heal_cost": 0, "threshold": 0, "effects": {
        "cooldown_multiplier": 1.0,
        "fail_rate_mod": 0,
        "earning_penalty": 0,
        "death_chance_mod": 0,
        "prison_chance_mod": 0,
        "guaranteed_fail": False
    }}

def get_fail_rate(guild_id: int, user: discord.User, action: str) -> int:
    """Calculate fail rate based on base rate and injury tier"""
    base_rate = FAIL_RATES.get(action, 0)
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    
    # Get the injury tier and its effects
    tier = get_injury_tier(injuries)
    
    # Add fail rate modifier from injury tier
    fail_rate_mod = tier["effects"]["fail_rate_mod"]
    
    # Cap the failure rate at 95% to always give a slim chance of success
    return min(95, base_rate + fail_rate_mod)

def get_outcome_chance(outcome_type, guild_id=None, user=None):
    """Get modified chance for a specific outcome type."""
    base_chance = OUTCOME_CHANCES.get(outcome_type, 0)
    
    # Apply modifiers if user is provided
    if guild_id and user:
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        injuries = user_data.get("injuries", 0)
        
        # Get injury tier and modifiers
        tier = get_injury_tier(injuries)
        if outcome_type == "death":
            return base_chance + tier["effects"]["death_chance_mod"]
        elif outcome_type == "prison":
            return base_chance + tier["effects"]["prison_chance_mod"]
    
    return base_chance

def get_modified_cooldown(guild_id: int, user: discord.User, base_cooldown: int) -> int:
    """Calculate modified cooldown based on injury tier"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    
    tier = get_injury_tier(injuries)
    cooldown_multiplier = tier["effects"]["cooldown_multiplier"]
    
    return int(base_cooldown * cooldown_multiplier)

def get_earning_multiplier(guild_id: int, user: discord.User) -> float:
    """Calculate earning multiplier based on injury tier (lower means less earnings)"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    
    tier = get_injury_tier(injuries)
    earning_penalty = tier["effects"]["earning_penalty"]
    
    return 1.0 - earning_penalty

def get_death_chance_modifier(guild_id: int, user: discord.User) -> int:
    """Get death chance modifier from injury tier"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    
    tier = get_injury_tier(injuries)
    return tier["effects"]["death_chance_mod"]

def get_prison_chance_modifier(guild_id: int, user: discord.User) -> int:
    """Get prison chance modifier from injury tier"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    
    tier = get_injury_tier(injuries)
    return tier["effects"]["prison_chance_mod"]

def get_escape_chance_modifier(guild_id: int, user: discord.User) -> int:
    """Get escape chance debuff based on injury tier"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    tier = get_injury_tier(injuries)

    # Fixed escape chance debuffs based on injury tier
    if tier["name"] == "Critical Condition":
        return -25
    elif tier["name"] == "Needs Surgery":
        return -15
    elif tier["name"] == "Moderate Injury":
        return -5
    elif tier["name"] == "Light Injury":
        return -3
    return 0

def get_heal_cost(injuries: int) -> int:
    """Calculate the cost to heal based on injury tier"""
    tier = get_injury_tier(injuries)
    return tier["heal_cost"]

def add_injury(guild_id: int, user: discord.User) -> int:
    """Add an injury to the user and return their new injury count"""
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user.id)
    
    # Get user data (auto-creates if not exists)
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    
    guild_data[user_key]["injuries"] = guild_data[user_key].get("injuries", 0) + 1
    guild_data[user_key]["injured"] = True
    DataService.save_guild_data(guild_id, guild_data)
    
    return guild_data[user_key]["injuries"]

def heal_injuries(guild_id: int, user: discord.User) -> None:
    """Heal all injuries from the user"""
    guild_data = DataService.load_guild_data(guild_id)
    user_key = str(user.id)
    if user_key not in guild_data:
        # Create default user data
        user_data = {
            "user_id": user.id,
            "username": user.display_name,
            "pockets": 0,
            "savings": 50,  # Default starting balance
            "cooldowns": {},
            "injured": False,
            "injuries": 0,
            "prison": None,
            "last_robbed": 0
        }
        guild_data[user_key] = user_data
    
    guild_data[user_key]["injuries"] = 0
    guild_data[user_key]["injured"] = False
    DataService.save_guild_data(guild_id, guild_data)

def get_injury_status(guild_id: int, user: discord.User) -> dict:
    """Get the user's injury status including tier and effects"""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    injuries = user_data.get("injuries", 0)
    tier = get_injury_tier(injuries)
    
    return {
        "injuries": injuries,
        "tier": tier["name"],
        "heal_cost": tier["heal_cost"],
        "effects": tier["effects"]
    }

@CommandRegistry.register_cog("economy")
class InjuryCommands(commands.Cog):
    """Provides commands for checking player injury status."""
    
    def __init__(self, bot):
        self.bot = bot
        self.debug = DebugTools.get_debugger("injury_commands")
        self.debug.log("Initializing InjuryCommands")
        
        # Import inside method to avoid circular imports
        from ..economy_base import EconomyCog
        self.cog_base = EconomyCog(bot)
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.status]
    
    @app_commands.command(name="status", description="Check your injury status and other conditions.")
    @command_error_handler
    async def status(self, interaction: discord.Interaction, member: discord.Member = None):
        """Check your or another member's status and condition."""
        # Default to the user if no member specified
        member = member or interaction.user
        
        # Get user data
        user_data = DataService.get_user_data(interaction.guild.id, member.id, member.display_name)
        
        # Get injury status using local function
        injury_status = get_injury_status(interaction.guild.id, member)
        
        prison = user_data.get("prison")
        prison_text = ""
        if prison:
            current_time = int(time.time())
            release_time = prison.get('release_time', 0)
            
            if current_time >= release_time:
                guild_data = DataService.load_guild_data(interaction.guild.id)
                guild_data[str(member.id)]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                if member.id == interaction.user.id:
                    await self.cog_base.send_embed(
                        interaction, "Prison Release", 
                        f"{member.mention}, you have served your time and have been released from hell...",
                        discord.Color.green()
                    )
                    return
            else:
                release_str = datetime.datetime.fromtimestamp(release_time).strftime('%Y-%m-%d %H:%M:%S')
                prison_text = f"\nImprisoned with the ***{prison['tier']}*** until: **{release_str}**"
        
        effects_text = "None"
        if injury_status["injuries"] > 0:
            effects = []
            
            if injury_status["tier"] == "Critical Condition":
                effects_text = "you should be dead..."
            else:
                if injury_status["effects"]["cooldown_multiplier"] > 1:
                    effects.append(f"Cooldowns +{int((injury_status['effects']['cooldown_multiplier']-1)*100)}%")
                if injury_status["effects"]["fail_rate_mod"] > 0:
                    effects.append(f"Fail rate +{injury_status['effects']['fail_rate_mod']}%")
                if injury_status["effects"]["earning_penalty"] > 0:
                    effects.append(f"Earnings -{int(injury_status['effects']['earning_penalty']*100)}%")
                if injury_status["effects"]["death_chance_mod"] > 0:
                    effects.append(f"Death chance +{injury_status['effects']['death_chance_mod']}%")
                if injury_status["effects"]["prison_chance_mod"] > 0:
                    effects.append(f"Prison chance +{injury_status['effects']['prison_chance_mod']}%")
                
                effects_text = ", ".join(effects)
        
        desc = (f"**Status for {member.mention}**\n"
                f"Condition: **{injury_status['tier']}**\n"
                f"Healing Cost: {injury_status['heal_cost']} Medals\n"
                f"Effects: {effects_text}{prison_text}")
        
        await self.cog_base.send_embed(interaction, "User Status", desc, discord.Color.blue())