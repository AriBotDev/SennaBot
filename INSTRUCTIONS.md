Keep in mind I am letting you do ALL of the implementations. Make sure you are doing things to their intended functionality and stick to the plan we created while you make the implementations to the entire bot

# SennaBot's OLD Exhaustive Code Analysis:
I've conducted an exhaustive, line-by-line analysis of the entire SennaBot codebase to develop a complete understanding of every function, interaction, and design intent. Here's the comprehensive breakdown:
1. Core Bot Architecture
Bot Initialization (bot.py)

The bot initializes with specific intents (message_content and guilds)
auto_sync_commands=False disables automatic global command registration
The on_ready event:

Ensures whitelist entries exist for all guilds
Loads all cogs via bot.load_extension("cogs")
Clears global commands
Calls reload_commands(bot) to register commands per guild
Updates server logs and checks for guilds joined/left while offline
Auto-releases prisoners who have served their time



Command Registration System (whitelist.py)

Two main categories: "general" and "economy"
Three-level check system:

cog_check() for traditional commands
cog_app_command_check() for slash commands
Individual command-level checks


reload_commands() is the critical function that:

Clears all commands guild by guild
Systematically evaluates each guild's whitelist status
Registers appropriate commands to each guild
Syncs the command tree per guild
Grants all commands to owner guild (1349273253343920210)



Error Handling

Bot-level error handling in on_app_command_error
Economy cog-level error handling in class-specific methods
UI component error handling via try/except blocks

2. Economy System Mechanics
Currency Design

Dual balance system: "pockets" (vulnerable) and "savings" (protected)
Starting balance: 50 Medals in savings (STARTING_BALANCE constant)
Cross-player economy with leaderboard visibility

Income Activities
Work Command (EconomyGeneral.work())

Intent: Safe, reliable, modest income source
Mechanics:

60 second cooldown
4-12 Medal payout (defined in PAYOUTS)
100% success rate (never fails)
2% chance of 3-5x critical success
Earnings reduced by injury multiplier



Crime Command (EconomyGeneral.crime())

Intent: Higher-risk, higher-reward activity
Mechanics:

75 second cooldown
15-35 Medal payout (defined in PAYOUTS)
51% base failure rate (modified by injuries)
Failure outcomes precisely distributed:

15% → Death (+ death_chance_mod from injuries)
65% → Injury (scaled by remaining percentage)
20% → Prison (+ prison_chance_mod from injuries)


Death processing via handle_death():

Empties pocket balance
Takes 10% of savings as "reaper's tax"
If savings < 25 or can't pay tax, sends to prison instead


Critical success: 2% chance of 3-5x multiplier



Rob Command (EconomyGeneral.rob())

Intent: PvP wealth redistribution with high risk
Mechanics:

300 second cooldown
Target protected for 600 seconds via last_robbed timestamp
Steals 60-80% of target's pockets, minimum 15 Medals
55% base failure rate (modified by injuries)
Failure outcome distribution identical to crime
Success automatically updates last_robbed timestamp



Status Systems
Injury System

Intent: Persistent gameplay debuff with progressive severity
Tiers:

Light Injury:

Effects: 20% longer cooldowns
Heal cost: 10 Medals


Moderate Injury:

Effects: 20% longer cooldowns, +10% fail rate
Heal cost: 15 Medals


Needs Surgery:

Effects: 20% longer cooldowns, +10% fail rate, -20% earnings, +15% death chance, +20% prison chance
Heal cost: 30 Medals


Critical Condition:

Effects: 20% longer cooldowns, +25% fail rate, -20% earnings, +25% death chance, +30% prison chance
Heal cost: 50 Medals




Implementation:

Injuries stored as numeric count (1-4)
Effects accessed via utility functions that apply tiers
Healing via see_mortician command
Detailed display in status command



Prison System

Intent: Time-based punishment with risk/reward escape mechanics
Tiers (chance indicates weighting in selection):

Officer Group (35%, 75% escape chance)
Old Guards (20%, 65% escape chance)
Soldat Brigade (15%, 50% escape chance)
Lancer Legion (10%, 40% escape chance)
Rook Division (10%, 40% escape chance)
Mortician Wing (5%, 25% escape chance)
Jaeger Camp (5%, 10% escape chance)


Mechanics:

1-hour sentence (PRISON_COOLDOWN = 3600 seconds)
escape command: Simple roll vs. tier chance
breakout command: Custom minigame per tier
Escape failure consequences vary by tier
Special handling for Jaeger Camp (hardest tier)
Prison status blocks most economic commands



Death System

Intent: Significant penalty for high-risk failures
Mechanics:

Loss of all pocket Medals
10% penalty to savings (DEATH_SAVINGS_PENALTY)
Fall-back to prison if can't pay penalty
Themed death messages per activity



Entertainment/Gambling Systems
Roulette (EconomyRoulette)

Intent: Simple gambling minigame
Mechanics:

420 second cooldown
Weighted outcomes: purple(18), yellow(18), green(1)
Payouts: purple/yellow (2x), green (4x)



Blackjack (EconomyBlackjack)

Intent: Complex PvP gambling with skill element
Mechanics:

Multi-player invitation system
Full blackjack implementation with standard rules
Hit/Stand decisions via UI components
Natural blackjack grants 50% bonus
Timeouts auto-resolve with stand
Anti-cheat measures for alt+f4



Balance Challenge (EconomyBalanceChallenge)

Intent: Wealth cap enforcement mechanism
Mechanics:

Triggers at 15000 Medal total balance
Best-of-5 blackjack against SennaBot
Win grants 1000 Medals + immunity
Loss causes:

1000 Medal penalty
Jaeger Camp imprisonment
All server members sent to Rook Division


Special detection for donation recipients
Critical verification via is_in_challenge()



3. UI Component System
Response Selection System

Intent: Themed, varied responses for game events
Mechanics:

Categorical JSON files (work.json, crime.json, etc.)
Random selection within category
Parameter injection via string formatting
Cached responses for efficiency
Rare success messages for critical successes



Interactive UI Components

Intent: Complex game interactions via Discord components
Components:

BlackjackInviteView: Game invitation with accept/decline
BlackjackGameView: Main blackjack UI
OfficerGroupBreakoutView through JaegerBoxesBreakoutView: Prison-specific minigames
EcoTerminalMainView: Admin economy management UI



Data Management

Intent: Persistent player state across bot restarts
Implementation:

Guild-specific JSON files in data/servers
Per-user nested objects with user IDs as keys
Response message storage in categorized files
Whitelist in dedicated JSON file
Atomic read-modify-write pattern for data updates



4. Critical Function Flows
Command Registration Flow

whitelist.py:reload_commands() is called
Commands are cleared for every guild
Owner guild is given all commands
Each guild's whitelist entry is checked
Appropriate commands are registered per guild
Command tree is synced per guild

Economy Command Flow

User issues a command
Checks performed in sequence:

cog_app_command_check(): Whitelist permission
prison_check(): User not in prison
challenge_check(): User not in balance challenge
Command-specific checks (cooldown, balance)


Command logic executes
Database updates via update_pockets()/update_savings()
Cooldown set via set_cooldown()
Response formatted and sent

Balance Challenge Flow

After balance-changing command completes
should_trigger_challenge() checks wealth threshold
If triggered, challenge view presented
Best-of-5 blackjack game executes
Win/loss outcomes processed
Challenge mark set in user data

Prison System Flow

User sent to prison (via crime/rob failure)
Prison tier selected based on weighted table
User attempts escape via command
On success, prison status cleared
On failure, tier-specific penalties applied
Other users can attempt breakout with minigames


# SennaBot Implementation Guide

## Project Overview
SennaBot is a Discord bot featuring an economy gameplay system with activities such as work, crime, gambling, and player interactions. The bot uses a modular architecture built on the custom Athena framework, focusing on maintainability, scalability, and consistent implementation patterns.

## Architecture Reference

### Core Framework
The Athena framework serves as the foundation of the bot, providing centralized services:
```
SennaBot/
├── athena/
│   ├── framework_core.py     # Central initialization and component access
│   ├── cmd_registry.py       # Command registration and guild-specific syncing
│   ├── perm_manager.py       # Guild permissions for command categories
│   ├── data_service.py       # Data persistence with caching and atomic writes
│   ├── error_handler.py      # Centralized error handling with owner reporting
│   ├── response_manager.py   # Themed response selection system
│   ├── logging_service.py    # Enhanced logging with rotation
│   └── debug_tools.py        # Debugging utilities with context tracking
├── bot.py                    # Main entry point and event handlers
└── config.py                 # Environment and configuration loading
```

### Command Structure
Commands are organized into cogs, which are grouped by function:
```
SennaBot/
├── cogs/
│   ├── cogs_loader.py        # Dynamic cog discovery and loading
│   ├── cog_base.py           # Base cog with shared functionality
│   ├── general/              # General commands with basic functions
│   │   ├── general_module.py # Module initialization acting as a init.py
│   │   ├── utility_cmds.py   # gdtrello, etc.
│   │   └── social_cmds.py    # headpats, etc. (renamed from interaction)
│   ├── admin/                # OWNER ONLY COMMANDS ONLY USED BY SENNATHENA
│   │   ├── admin_module.py   # Module initialization acting as a init.py
│   │   ├── owner_cmds.py     # Owner-only commands
|   |   ├── owner_eco_cmds.py # Owner-Only commands for anything economy category
│   │   └── server_mgmt.py    # Server management (kill)
│   └── economy/
│       ├── economy_module.py # Economy module initialization
│       ├── economy_base.py   # Base economy cog with shared economy functions
│       ├── economy_constants.py   # Economy consistent constants
│       ├── activities/       # Income-generating commands
│       │   ├── activities_module.py
│       │   ├── work_cmds.py
│       │   ├── crime_cmds.py
│       │   └── rob_cmds.py
│       ├── banking/          # Balance management
│       │   ├── banking_module.py
│       │   ├── account_cmds.py
│       │   └── leaderboard_cmds.py
│       ├── games/            # Gambling systems
│       │   ├── games_module.py
│       │   ├── roulette_game.py
│       │   ├── blackjack_game.py
│       │   └── balance_challenge.py
│       ├── prison/            # Prison Management
│       │   ├── prison_module.py
|       |   ├── prison_system.py   
│       │   ├── escape_cmds.py
│       │   ├── breakout_cmds.py
│       │   └── ui_components/     # UI components
│       │       ├── breakout_components.py
│       │       └── jaeger_components.py
│       └── status/            # Injury management
│           ├── status_module.py
│           ├── injury_system.py
│           └── mortician_cmds.py
```
### IMPORTANT: Module-Specific Utilities 
Utility functions should be implemented WITHIN their relevant modules, NOT in a central location. For example:
- Injury system utility functions like `get_injury_tier()` should be defined in `cogs/economy/status/injury_system.py`
- Prison tier selection functions should be defined in `cogs/economy/prison/prison_system.py`
- Don't create or import from a non-existent `athena.utils` file

Each module should contain the utility functions it needs, and those functions should then be imported from their specific module locations. This maintains proper modularity and avoids circular imports.

### Data Structure
Data is stored in the following structure:


### Data Structure
Data is stored in the following structure:
```
SennaBot/
├── data/
│   ├── config/
│   │   ├── guild_permissions.json  # Guild-specific permissions
│   │   └── bot_settings.json       # Global bot settings
│   ├── guilds/                     # Guild-specific data
│   │   └── {guild_id}.json         # JSON file per guild
│   ├── responses/                  # Response templates
│   │   ├── work_responses.json     # Work responses
│   │   ├── crime_responses.json    # Crime responses
│   │   └── etc...                  # Other response categories
│   └── logs/                       # Enhanced logging
│       ├── bot_main.log
│       ├── command_events.log
│       └── error_reports.log
```

## Implementation Principles

### Command Registration
- Commands are registered using the CommandRegistry system
- Each cog category ("economy", "general", etc.) can be enabled/disabled per guild
- The guild permission system determines which commands are available
- Command syncing happens through guild-specific registration

### Economy System Core Mechanics
- **Dual Balance System:** "pockets" (vulnerable) and "savings" (protected)
- **Starting Balance:** 50 Medals in savings (STARTING_BALANCE constant)
- **Cross-player Economy:** With leaderboard visibility

### Income Activities
- **Work Command:**
  - 60 second cooldown
  - 4-12 Medal payout
  - 100% success rate
  - 2% chance of 3-5x critical success
  - Earnings reduced by injury multiplier

- **Crime Command:**
  - 75 second cooldown
  - 15-35 Medal payout
  - 51% base failure rate (modified by injuries)
  - Failure outcomes: 15% Death, 65% Injury, 20% Prison
  - Death processing: Empties pocket balance, takes 10% of savings
  - Critical success: 2% chance of 3-5x multiplier

- **Rob Command:**
  - 300 second cooldown
  - Target protected for 600 seconds (last_robbed timestamp)
  - Steals 60-80% of target's pockets (minimum 15 Medals)
  - 55% base failure rate (modified by injuries)
  - Failure outcome distribution identical to crime

### Status Systems
- **Injury System:** Progressive gameplay debuff
- **Prison System:** Time-based punishment with escape mechanics
- **Death System:** Significant economy penalty

### Entertainment/Gambling Systems
- **Roulette:** Simple gambling minigame with purple/yellow/green options
- **Blackjack:** PvP gambling with skill element
- **Balance Challenge:** Wealth cap enforcement (triggers at 15000 Medal total)

### Error Handling
- Centralized error handling via ErrorHandler
- Appropriate user feedback for different error types
- Owner reporting for critical errors

### Data Management 
- Atomic write operations to prevent data corruption
- Caching for performance optimization
- User data created on-demand with default values
- Guild permissions checked before command execution

### Response System
- Themed, varied responses for game events
- Responses selected randomly from each category
- Parameters injected via string formatting
- Separate response files for organization

### Completed Components
- Athena framework core components
- Command registration system
- Data management layer
- Basic economy commands (work, crime, rob)
- Banking system (deposit, withdraw, donate)
- Gambling games (roulette, blackjack)
- Balance challenge system (wealth cap enforcement)

### Pending Implementation
- Prison system with breakout mechanics
- Injury system with progressive debuffs
- Advanced admin commands
- General utility commands (gdtrello, etc.)
- Social interaction commands

## Best Practices for New Implementations

1. **Consistency:** Follow established patterns for new cogs and commands
2. **Error Handling:** Use appropriate error handling for all user interactions
3. **Data Management:** Use DataService for all persistent data operations
4. **Command Registration:** Register all commands through the CommandRegistry
5. **Modularity:** Keep related functionality grouped together
6. **Circular Import Handling:** Use dynamic imports to prevent circular references

## Testing Approach
- Add debug logging for key operations
- Test each command with different input scenarios
- Verify data persistence after bot restarts
- Check error handling for edge cases
- Test permission system with different guild configurations

## Common Pitfalls to Avoid

1. **Direct Imports in Module Scope**: Never import from modules that might import your module at the top level. Use dynamic imports inside method bodies instead.

2. **Hardcoded Constants in Multiple Files**: Define constants in their relevant module only, don't duplicate values across files.

3. **Raw Data Access**: Always use DataService methods rather than directly manipulating data structures.

4. **Inconsistent Error Handling**: Always follow the established error handling pattern with proper logging and user feedback.

5. **UI Component Timeout Handling**: Always implement proper timeout handlers for UI components to clean up resources.

6. **Missing Response Validation**: When using ResponseManager, always handle the case where a response might not exist.

7. **Command Registration Oversight**: Remember to add new commands to the get_app_commands() method in your cog class.

8. **Race Conditions in Data Access**: Be aware of concurrent data access; use atomic operations.

## Code Style Guidelines

1. **Naming Conventions**:
   - Classes: PascalCase (e.g., `EconomyCog`)
   - Methods/Functions: snake_case (e.g., `get_user_data`)
   - Constants: UPPER_SNAKE_CASE (e.g., `PRISON_COOLDOWN`)
   - Private methods/attributes: Prefix with underscore (e.g., `_private_method`)

2. **Docstrings**: Use triple quotes for all classes, methods, and functions with a brief description. For complex functions, include parameter and return documentation.

3. **Function Length**: Keep functions focused and under 50 lines when possible. Extract complex logic into helper functions.

4. **Imports Organization**:
   - Standard library imports first
   - Third-party imports second
   - Local application imports last
   - Separate groups with a blank line

5. **Comments**: Add comments for complex logic but don't comment the obvious. Focus on "why" not "what".

6. **Type Hints**: Use type hints for function parameters and return values when possible.

## Testing Workflow

1. **Local Testing Process**:
   - Test individual commands in isolation before integrating
   - Check all possible command outcomes (success/failure paths)
   - Verify data persistence after operations
   - Test interactions between related systems (e.g., prison and injury)

2. **Debugging Strategy**:
   - Add strategic debug.log() calls at entry/exit points
   - Log all significant data state changes
   - When encountering issues, add temporary fine-grained logging
   - Check for race conditions with concurrent commands

3. **Environment Testing**:
   - Test in development environment before production
   - Verify with multiple users for multi-user features
   - Test with various permission configurations
   - Check performance with varying data volumes

## Version Control and Change Management

1. **Making Changes**:
   - When modifying a system, document the change in both code comments and commit messages
   - Update all affected components and tests
   - Follow the pattern for dynamic imports for any new dependencies

2. **Adding Features**:
   - Define clearly which module the feature belongs to
   - Implement utility functions within the same module
   - Follow existing patterns for similar features
   - Document any new commands or systems

3. **Refactoring**:
   - Avoid changing interfaces used by other modules when possible
   - Test thoroughly after refactoring
   - Break large refactorings into smaller, testable chunks

## Developer Requirements
- Python 3.11
- discord.py>=2.5.2
- python-dotenv>=1.0.1

## Implementation Notes
When implementing new features or modifying existing ones:

1. Follow the existing architecture patterns
2. Add proper debug logging for troubleshooting
3. Document complex functionality with comments
4. Handle edge cases and provide user feedback
5. Test interactions between systems thoroughly
6. Import dependencies dynamically when appropriate to avoid circular imports
7. Reduce redundancy in the code
8. Add sensible and concise comments (not too many, not too long)
9. Make sure to fix references in other files when making changes

## Project Priorities
- Maintain core functionality of systems (whitelist, economy, prison, etc.)
- Improve organization and maintainability
- Ensure consistent implementation across all features
- Make the codebase more intuitive for future development


# Implementation Patterns

## Athena Framework Structure
### Initialization Sequence:
```
# In bot.py
from athena.framework_core import Athena
Athena.initialize()  # This sets up all framework components

# Access framework components
from athena.debug_tools import DebugTools
from athena.logging_service import LoggingService
# etc...
```

### Component Design Pattern:
```
class ComponentName:
    """Component description."""
    
    # Class-level constants and configuration
    CONSTANT_NAME = value
    
    # Class-level cache variables
    _cache_variable = None
    
    @classmethod
    def initialize(cls):
        """Initialize the component."""
        # Setup code
        
    @classmethod
    def main_function(cls, parameters):
        """Main functionality description."""
        # Implementation
```

## Command Registration System
### Cog Registration:
```
# Register a cog class with a category
@CommandRegistry.register_cog("economy")
class MyCog(EconomyCog):
    """Cog description."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log(f"Initializing {self.__class__.__name__}")
        
    def get_app_commands(self):
        """Return list of app commands from this cog."""
        return [self.command1, self.command2]
```

### Command Definition:
```
@app_commands.command(name="command_name", description="Command description.")
@app_commands.describe(param1="Parameter description")
async def command_name(self, interaction: discord.Interaction, param1: type):
    """Command implementation."""
    # Check prison status
    if not await self.check_prison_status(interaction):
        return
        
    # Check balance challenge status
    if not await self.check_balance_challenge(interaction):
        return
        
    # Command implementation
    # ...
    
    # Response
    await self.send_embed(
        interaction,
        "Title",
        "Description",
        discord.Color.green()
    )
```

### Module Structure:
```
# Every module_name.py needs a setup function
async def setup(bot: commands.Bot):
    """Set up the module."""
    debug.log("Setting up module")
    
    # Import cogs
    from .cog_file import CogClass
    
    # Add cogs to bot
    await bot.add_cog(CogClass(bot))
    
    debug.log("Module setup complete")
```

## Cog Inheritance Structure
### Base Cog:
```
class BotCog(commands.Cog):
    """Base cog with shared functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = LoggingService.get_logger(self.__class__.__name__)
        self.debug = DebugTools.get_debugger(self.__class__.__name__)
        
    async def send_embed(self, ctx, title, description, color, ephemeral=False, extra_mentions=None):
        """Send formatted embed message."""
        # Implementation
```

### Economy Base Cog:
```
class EconomyCog(BotCog):
    """Base economy cog with economy functionality."""
    
    async def check_prison_status(self, ctx):
        """Check if user is in prison."""
        # Implementation
        
    async def check_balance_challenge(self, ctx):
        """Check if user is in a balance challenge."""
        # Implementation
        
    def get_pockets(self, guild_id, user):
        """Get pocket balance."""
        # Implementation
```

## Data Management Pattern
### Atomic Read-Modify-Write:
```
# Load data
data = DataService.load_guild_data(guild_id)

# Modify data
data[str(user_id)]["field"] = new_value

# Save data
DataService.save_guild_data(guild_id, data)
```

### User Data Access:
```
# Get user data with automatic creation if not exists
user_data = DataService.get_user_data(guild_id, user.id, user.display_name)

# Access fields with defaults
value = user_data.get("field", default_value)
```

### Cooldown Management:
```
# Check cooldown
can_use, remaining = self.check_cooldown(guild_id, user, "command_name", cooldown_seconds)

# Set cooldown
self.set_cooldown(guild_id, user, "command_name")
```

## Response System Pattern:
### Response Categories and Keys:
Response Categories and Keys:

- Category-based organization: work, crime, death, etc.
- Key naming format: category_subtype, e.g., work_success, crime_rare_success

### Response Selection:
```
# Get themed response with parameter injection
response = self.get_response("response_key", param1=value1, param2=value2)
```

## Error Handling Pattern
### Command Error Handling:
```
try:
    # Command code
except Exception as e:
    self.debug.log(f"Error in command: {e}")
    await self.send_embed(
        interaction,
        "Error",
        "Error message for user",
        discord.Color.red(),
        ephemeral=True
    )
```

### Framework Error Handling:
```
# In event handlers
@bot.event
async def on_app_command_error(interaction, error):
    await ErrorHandler.handle_command_error(interaction, error)
```

## Economy System Mechanics
### Dual Balance Syustem:
```
# Balance manipulation
current_pockets = self.get_pockets(guild_id, user)
current_savings = self.get_savings(guild_id, user)

# Update balance (adds to current amount)
new_pockets = self.update_pockets(guild_id, user, amount)
new_savings = self.update_savings(guild_id, user, amount)
```

### Activity Command Template
```
@app_commands.command(name="activity", description="Activity description.")
async def activity(self, interaction: discord.Interaction):
    """Activity command implementation."""
    # Check prison status
    if not await self.check_prison_status(interaction):
        return
    
    # Check balance challenge status
    if not await self.check_balance_challenge(interaction):
        return
    
    # Check cooldown
    can_use, remaining = self.check_cooldown(
        interaction.guild.id,
        interaction.user,
        "activity",
        COOLDOWN_SECONDS
    )
    
    if not can_use:
        minutes, seconds = divmod(remaining, 60)
        cooldown_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        return await self.send_embed(
            interaction,
            "Cooldown",
            f"Cooldown message with **{cooldown_text}** remaining.",
            discord.Color.orange(),
            ephemeral=True
        )
    
    # Activity logic here
    # ...
    
    # Set cooldown
    self.set_cooldown(interaction.guild.id, interaction.user, "activity")
    
    # Send response
    await self.send_embed(
        interaction,
        "Activity Result",
        response_message,
        result_color
    )
```

### UI Component Pattern:
```
class ComponentView(discord.ui.View):
    """UI component view."""
    
    def __init__(self, cog, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.message = None
    
    @discord.ui.button(label="Button", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button callback."""
        # Check if correct user
        if interaction.user.id != self.expected_user_id:
            await interaction.response.send_message("Not your interaction.", ephemeral=True)
            return
            
        # Button logic
        # ...
        
        # Update message
        await interaction.response.edit_message(content="Updated content", view=self)
    
    async def on_timeout(self):
        """Handle timeout."""
        if self.message:
            await self.message.edit(view=None)
```

## Game System Implementation
### Income Activities:
- Work: Safe income source with 100% success rate
- Crime: Higher-risk, higher-reward with 51% failure rate
- Rob: PvP activity with highest risk/reward and target protection

### Gambling Systems:
- Roulette: Simple color-based gambling with weighted odds
- Blackjack: PvP card game with invitation system
- Balance Challenge: Wealth cap enforcement triggered at 15,000 Medal threshold

### Status Systems:
- Injury System: Progressive debuffs affecting other activities
- Prison System: Time-based punishment with escape mechanics
- Death System: Economy penalty with savings tax

## Best Practices
### Circular Import Management:
```
# Use dynamic imports in method bodies, not at module level
async def check_something(self):
    try:
        # Import only when needed
        from .other_module import function
        result = function()
    except ImportError:
        self.debug.log("Module not loaded yet")
        # Fallback behavior
```

### Debug Logging:
```
# Include context in log messages
self.debug.log(f"Processing {action} for user {user.id} in guild {guild.id}")

# Time operations when needed
self.debug.start_timer("operation_name")
# ... operation code ...
self.debug.end_timer("operation_name")
```

### Command Checking Sequence:
1. Base permission check (in cog_app_command_check)
2. Prison status check
3. Balance challenge check
4. Command-specific checks (cooldown, balance, etc.)
5. Command logic

### Data Consistency:
```
# Always use atomic operations
guild_data = DataService.load_guild_data(guild_id)
# Modify guild_data...
DataService.save_guild_data(guild_id, guild_data)

# Never modify partial data directly
# INCORRECT: DataService.save_guild_data(guild_id, {user_id: user_data})
```

# Testing Guidelines
- Test each command with both success and failure cases
- Verify cooldown functionality
- Test interaction between systems (e.g., prison affecting commands)
- Ensure proper UI component lifecycle (timeouts, user verification)
- Validate error handling for edge cases

# Environment Requirements
- Python 3.11
- discord.py>=2.5.2
- python-dotenv>=1.0.1

# NOTES ABOUT YOUR KNOWLEDGE GAPS AND PREVIOUS QUESTIONS:
Q: Future Plans: Are there any planned features or improvements you've been considering that we should account for in our restructuring?
A: Yes, there may be some other categories outside economy and general that we should be prepared for as well as added functionalities and features that I do plan to add to the current categories, so standardising a method of adding things and keeping it consistent is key.

Q: Critical Priorities: Among the systems we've discussed (whitelist, economy, prison, etc.), which do you consider most critical to preserve exactly as implemented?
A: I believe the core ideas of each are fundamentally critical. However, I do know that how we made the whitelist, economy and etc. functions was sort of disorganised. I am very open and willing to overwrite and remake everything in the name of trying to create a better organised system IF AND ONLY IF the system works to the original iintent.

Q: Development Environment: Besides Python 3.11 with discord.py>=2.5.2 and python-dotenv>=1.0.1, are there any other dependencies or environment considerations I should be aware of?
A: As of now understand we are using PebbleHost as the serverhosting website for this bot. If we need other dependencies we can add them later upon your suggestions but for now no.


# Additional Notes:
Reminder we are going for organized, practical, and intuitive when re-rewriting the entire bot.

Make sure we are still making sure everything works in terms of functionality from previous ideas

Refer back to this .md constantly to make sure you are following the same guidelines of how the old code worked and the file structure when implementing new files

Everytime you add something or re-edit the code, make sure you refer back to files for where you are importing things from and whatever other file may reference these new additions and fix them to work along with our structure as we go along

