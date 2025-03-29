# SennaBot Debug Guide

This document identifies current issues in SennaBot's codebase and provides detailed solutions. Use this as a reference when improving the bot's stability and performance.

## Current Critical Issues

### 1. Circular Import Problems

**Issue:** Despite function-level imports, some modules still have circular dependencies that could cause runtime errors.

**Files Affected:**
- `economy_base.py`
- `prison_system.py`
- `injury_system.py`
- `balance_challenge.py`

**Fix:**
Restructure imports to break circular dependencies. For example, in `economy_base.py`:

```python
async def check_balance_challenge(self, ctx):
    """Check if user is in a balance challenge."""
    user_id = ctx.user.id
    
    # Import function directly rather than the entire module
    try:
        # Use a simple function that only needs the user ID
        from .games.balance_challenge import is_in_challenge
        
        # Check if user is in an active challenge
        if is_in_challenge(user_id):
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
```

Also, consider creating a central module for common constants to reduce cross-module dependencies:

```python
# economy_constants.py
"""
Constants shared across economy modules.
"""

# Prison constants
PRISON_COOLDOWN = 3600  # 1 hour
ESCAPE_COOLDOWN = 120   # 2 minutes
BREAKOUT_COOLDOWN = 300 # 5 minutes

# Failure rates
FAIL_RATES = {
    "crime": 51,
    "rob": 55
}

# Outcome chances
OUTCOME_CHANCES = {
    "death": 15,    # 15% chance for death on failure
    "injury": 65,   # 65% chance for injury on failure
    "prison": 20    # 20% chance for prison on failure
}

# Death penalty
DEATH_SAVINGS_PENALTY = 0.10  # 10% of savings
```

### 2. Race Conditions in Data Handling

**Issue:** Some operations in UI components directly modify data without proper synchronization, which can lead to data corruption when multiple operations happen simultaneously.

**Files Affected:**
- `breakout_components.py`
- `jaeger_components.py`
- `balance_challenge.py`

**Fix:**
Implement proper synchronization for all data operations. For example, in `balance_challenge.py`:

```python
# Create a thread-safe lock mechanism
_donation_lock = threading.Lock()

# Replace this code in BalanceChallengeCog.on_app_command_completion
async def on_app_command_completion(self, interaction, command):
    try:
        # Special handling for donate command 
        if interaction.command and interaction.command.name == "donate":
            # Extract the target from options
            target = None
            
            try:
                options = interaction.data.get("options", [])
                for option in options:
                    if option.get("name") == "target":
                        target_id = option.get("value")
                        self.debug.log(f"Found target ID: {target_id}")
                        
                        # Try to resolve the target using fetch_user first
                        target = await self.bot.fetch_user(int(target_id))
                        if not target:
                            self.debug.log(f"Failed to fetch user with ID {target_id}")
                            continue
                            
                        # Try to resolve as member if possible
                        try:
                            member = await interaction.guild.fetch_member(int(target_id))
                            if member:
                                target = member
                        except:
                            # Continue with the user object if we can't get the member
                            pass
                            
                        self.debug.log(f"Resolved target: {target.display_name if target else 'None'}")
                        break
            except Exception as e:
                self.debug.log(f"Error extracting or resolving target from donate command: {e}")
            
            if target and target.id != interaction.user.id:
                # Use thread-safe locking instead of a simple dictionary
                target_id = target.id
                acquire_lock = False
                
                # Try to acquire lock for this target
                with _donation_lock:
                    if target_id in self.donation_check_locks:
                        self.debug.log(f"Target {target_id} already being checked, skipping")
                    else:
                        # Set lock for this target
                        self.donation_check_locks[target_id] = True
                        acquire_lock = True
                
                if acquire_lock:
                    try:
                        # Wait longer for the donation to complete and balances to update
                        self.debug.log(f"Waiting for donation to complete...")
                        await asyncio.sleep(3.0)
                        
                        # Check if the target now meets the challenge threshold
                        result = await balance_challenge_manager.trigger_challenge_for_donation_target(
                            self.bot, interaction.guild, target
                        )
                        self.debug.log(f"Challenge trigger result for {target.display_name}: {result}")
                    finally:
                        # Clear the lock regardless of the outcome
                        with _donation_lock:
                            if target_id in self.donation_check_locks:
                                del self.donation_check_locks[target_id]
            else:
                self.debug.log(f"Target not found or is self")
```

### 3. Inconsistent Prison and Escape Handling

**Issue:** Escape chance modifiers are calculated differently in `prison_system.py` and `escape_cmds.py`, leading to unpredictable escape success rates.

**Files Affected:**
- `prison_system.py`
- `escape_cmds.py`
- `injury_system.py`

**Fix:**
Standardize the escape chance calculation by moving it to a single location:

```python
# In injury_system.py (as a central location)
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
    
    # Apply standard penalties based on injury level
    if injuries >= 4:  # Critical Condition
        return -25
    elif injuries >= 3:  # Needs Surgery
        return -15
    elif injuries >= 2:  # Moderate Injury
        return -5
    elif injuries >= 1:  # Light Injury
        return -3
    
    return 0
```

Then update `escape_cmds.py` to use this function:

```python
# In escape_cmds.py
from ..status.injury_system import get_escape_chance_modifier

# Later in the escape command method
# Get base escape chance from tier
base_escape_chance = tier[2]

# Modify escape chance based on injury tier using the centralized function
escape_chance_mod = get_escape_chance_modifier(interaction.guild.id, interaction.user.id)
escape_chance = base_escape_chance + escape_chance_mod

# Ensure escape chance doesn't go below 5%
escape_chance = max(5, escape_chance)
```

### 4. UI Component Resource Cleanup

**Issue:** Several UI components have incomplete `on_timeout()` handlers that don't properly clean up resources, which can lead to memory leaks and dangling references.

**Files Affected:**
- `blackjack_game.py`
- `breakout_components.py`
- `jaeger_components.py`

**Fix:**
Implement proper cleanup in all UI components. For example, in `BlackjackGameView`:

```python
async def on_timeout(self):
    """Handle timeout of the game view."""
    try:
        # Check if the game was already completed
        if self.finished:
            # Game already finished, just clean up any remaining messages
            await self.cleanup_messages()
            return
                
        # If a game is still in progress when the view times out, cancel it
        await self.cancel_game()
        
        # Explicitly clean up references
        self.game = None
        self.cog = None
        self.channel = None
        self.game_message = None
        self.turn_messages = []
        self.turn_notifications = {}
    except Exception as e:
        debug.log(f"Error in timeout handler: {e}")
```

For `JaegerBoxesBreakoutView`, fix the `on_timeout` method:

```python
async def on_timeout(self):
    """Handle timeout of the component."""
    try:
        # Get current guild and user data
        guild_id = self.interaction.guild.id
        user_id = self.interaction.user.id
        user = self.interaction.user
        
        # Clear pocket money
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        
        with DataService.get_guild_lock(guild_id):
            pockets_before = self.cog.get_pockets(guild_id, user)
            self.cog.update_pockets(guild_id, user, -pockets_before)
                        
            # Take 25% of savings
            savings = self.cog.get_savings(guild_id, user)
            savings_penalty = int(savings * 0.25)
            
            # Apply penalty
            if savings <= 0 or savings_penalty <= 0:
                self.cog.update_savings(guild_id, user, -75)
                savings_penalty = 75
            else:
                self.cog.update_savings(guild_id, user, -savings_penalty)
            
            # Reload guild data after updates
            guild_data = DataService.load_guild_data(guild_id)
            user_key = str(user_id)
            
            # Free from prison and clear injuries
            if user_key in guild_data:
                guild_data[user_key]["prison"] = None
                guild_data[user_key]["injuries"] = 0
                guild_data[user_key]["injured"] = False
                DataService.save_guild_data(guild_id, guild_data)
        
        embed = discord.Embed(
            title="Impatient Wolves",
            description=f"The Jaeger's grew impatient of your silly games.\n\n**They have lobbed your head off.**\n\nTaking your **All** Medals from your pockets and **{savings_penalty}** Medals from savings...",
            color=discord.Color.dark_red()
        )
        
        # Safely edit message with try-except
        try:
            await self.interaction.edit_original_response(
                content=f"<@{user_id}>",
                embed=embed,
                view=None
            )
        except Exception as e:
            debug.log(f"Error editing message in timeout handler: {e}")
            # Try followup message as fallback
            try:
                await self.interaction.followup.send(
                    content=f"<@{user_id}>",
                    embed=embed
                )
            except:
                pass
                    
    except Exception as e:
        debug.log(f"Error in timeout handler: {e}")
        
    finally:
        # Clean up references
        self.cog = None
        self.interaction = None
        self.user = None
        self.message = None
```

### 5. Negative Balance Handling Inconsistency

**Issue:** In `economy_base.py`, `allow_negative_pockets` and `allow_negative_savings` are always set to True, but commands like deposit/withdraw in `account_cmds.py` assume balances can't be negative.

**Files Affected:**
- `economy_base.py`
- `account_cmds.py`

**Fix:**
Make negative balance handling consistent by updating `economy_base.py`:

```python
def update_pockets(self, guild_id, user, amount):
    """Update a user's pocket balance with thread safety."""
    with DataService.get_guild_lock(guild_id):
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        current_balance = user_data.get("pockets", 0)
        
        # For withdrawals, always allow negative balances (allows debt)
        # This is consistent with how account_cmds.py handles it
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
        
        # For withdrawals, always allow negative balances (allows debt)
        # This is consistent with how account_cmds.py handles it
        user_data["savings"] = current_balance + amount
        guild_data = DataService.load_guild_data(guild_id)
        guild_data[str(user.id)] = user_data
        DataService.save_guild_data(guild_id, guild_data)
        return user_data["savings"]
```

Also, make sure all commands check for negative balances properly:

```python
# In deposit command in account_cmds.py
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
```

### 6. Error Handling Gaps

**Issue:** The `command_error_handler` decorator isn't used consistently across all commands, and some UI component callbacks don't have proper error handling.

**Files Affected:**
- Various command implementations
- UI component classes

**Fix:**
Apply the error handler decorator consistently to all commands:

```python
# In any command implementation
@app_commands.command(name="command_name", description="Command description.")
@command_error_handler
async def command_name(self, interaction: discord.Interaction):
    """Command implementation."""
    # ...
```

Add proper error handling to UI component callbacks:

```python
# Example for a button callback
@discord.ui.button(label="Button", style=discord.ButtonStyle.primary)
async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
    try:
        # Check if correct user
        if interaction.user.id != self.expected_user_id:
            await interaction.response.send_message("Not your interaction.", ephemeral=True)
            return
            
        # Button logic
        # ...
        
        # Update message
        await interaction.response.edit_message(content="Updated content", view=self)
    except Exception as e:
        debug.log(f"Error in button callback: {e}")
        try:
            # Send error message to user
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while processing this interaction.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while processing this interaction.",
                    ephemeral=True
                )
        except:
            pass
```

### 7. Initialization Order Dependencies

**Issue:** The initialization sequence in `bot.py` might access components before they're properly initialized.

**Files Affected:**
- `bot.py`
- `framework_core.py`

**Fix:**
Implement a proper dependency management system in `framework_core.py`:

```python
@classmethod
def initialize(cls):
    """Initialize the Athena framework."""
    if cls.initialized:
        print("Athena framework already initialized")
        return
    
    print(f"Initializing Athena framework v{cls.VERSION}")
    
    # Ensure data directories exist
    cls._ensure_directories()
    
    # Define initialization order
    init_sequence = [
        ('debug_tools', lambda: DebugTools.get_debugger("framework")),
        ('logging_service', lambda: cls._init_logging()),
        ('data_service', lambda: DataService.initialize()),
        ('perm_manager', lambda: None),  # No explicit initialization needed
        ('cmd_registry', lambda: None),  # No explicit initialization needed
        ('response_manager', lambda: ResponseManager.initialize()),
        ('error_handler', lambda: None)  # No explicit initialization needed
    ]
    
    # Execute initialization sequence
    for component_name, init_func in init_sequence:
        try:
            result = init_func()
            if component_name == 'debug_tools':
                cls.debug = result
                cls.debug.log(f"Initializing Athena framework v{cls.VERSION}")
            elif component_name == 'logging_service':
                cls.logging_service = result
            # Store other components as they're initialized
        except Exception as e:
            print(f"Error initializing component {component_name}: {e}")
            # Continue initialization of other components
    
    # Import and store references to all components
    from .data_service import DataService
    from .perm_manager import PermissionManager
    from .cmd_registry import CommandRegistry
    from .response_manager import ResponseManager
    from .error_handler import ErrorHandler
    
    # Store references
    cls.data_service = DataService
    cls.perm_manager = PermissionManager
    cls.cmd_registry = CommandRegistry
    cls.response_manager = ResponseManager
    cls.error_handler = ErrorHandler
    
    cls.initialized = True
    cls.debug.log("Athena framework initialization complete")

@classmethod
def _init_logging(cls):
    """Initialize logging service."""
    from .logging_service import LoggingService
    LoggingService.initialize()
    return LoggingService
```

And modify `bot.py` to wait for full initialization:

```python
# In bot.py, on_ready event
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    try:
        logger.info(f"✅ Logged in as {bot.user}!")
        debug.log(f"Bot is ready as {bot.user}!")
        print(f"✅ Logged in as {bot.user}!")
        
        # Make sure framework is fully initialized
        if not Athena.initialized:
            debug.log("Athena framework not fully initialized, waiting...")
            # Wait a bit to ensure initialization is complete
            await asyncio.sleep(1)
        
        # Set bot instance in error handler for event error reporting
        ErrorHandler.set_bot_instance(bot)
        ErrorHandler.set_owner_id(config.OWNER_ID)
        
        # Create guild permission entries for all guilds
        for guild in bot.guilds:
            PermissionManager.ensure_guild_entry(
                PermissionManager.load_permissions(),
                str(guild.id),
                guild.name
            )
        PermissionManager.save_permissions()
        
        # Load all cogs
        debug.log("Loading cogs...")
        await bot.load_extension("cogs")
        
        # Clear global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        debug.log("Cleared global commands")
        
        # Sync commands for all guilds
        await CommandRegistry.sync_all_guilds(bot)
        
        # Process any prisoners who should be released
        await process_prison_releases()
        
        logger.info("Bot initialization complete")
        debug.log("Bot initialization complete")
    except Exception as e:
        logger.error(f"Error during bot initialization: {e}")
        debug.log(f"Error during bot initialization: {e}")
        ErrorHandler.handle_event_error("on_ready", e)
```

### 8. Game State Management Issues

**Issue:** In `blackjack_game.py`, the `cleanup_game` method doesn't always properly clean up all game references, which can lead to "zombie" games or memory leaks.

**Files Affected:**
- `blackjack_game.py`

**Fix:**
Improve the `cleanup_game` method in `BlackjackGameView`:

```python
async def cleanup_game(self, message=None):
    """Clean up all resources for this game."""
    try:
        # Unregister from active games
        self.unregister_game()
        
        # Clean up turn messages
        await self.cleanup_messages()
        
        # Clean up game message if not already handled
        if self.game_message and not message:
            try:
                await self.game_message.delete()
            except Exception as e:
                debug.log(f"Error deleting game message: {e}")
                # Don't throw, continue cleanup
            
        # Clear any stored references
        for player_id in self.turn_notifications:
            try:
                # Stop all pending notifications
                notification = self.turn_notifications[player_id]
                notification.stop()
            except Exception as e:
                debug.log(f"Error stopping notification: {e}")
                
        # Clear all member references
        self.game = None
        self.cog = None
        self.channel = None
        self.game_message = None
        self.turn_messages = []
        self.turn_notifications = {}
    except Exception as e:
        debug.log(f"Error in game cleanup: {e}")
```

Also, add periodic cleanup of abandoned games:

```python
# Add this function to blackjack_game.py
async def cleanup_abandoned_games():
    """Check for and clean up any abandoned games."""
    current_time = time.time()
    games_to_remove = []
    
    for game_key, game in ACTIVE_GAMES.items():
        # Check if game view has a last_activity timestamp
        if hasattr(game, 'last_activity') and (current_time - game.last_activity) > 300:  # 5 minutes
            games_to_remove.append(game_key)
            try:
                # Try to cancel the game
                game_view = getattr(game, 'view', None)
                if game_view:
                    asyncio.create_task(game_view.cancel_game())
            except Exception as e:
                debug.log(f"Error cleaning up abandoned game {game_key}: {e}")
    
    # Remove games from active games dict
    for key in games_to_remove:
        try:
            del ACTIVE_GAMES[key]
            debug.log(f"Removed abandoned game: {key}")
        except KeyError:
            pass
```

### 9. Balance Challenge Triggers

**Issue:** In `balance_challenge.py`, the `on_app_command_completion` handler has complex logic that might not handle all edge cases.

**Files Affected:**
- `balance_challenge.py`

**Fix:**
Simplify and improve the handler logic:

```python
@commands.Cog.listener()
async def on_app_command_completion(self, interaction, command):
    try:
        # Skip processing if not in a guild
        if not interaction.guild:
            return
            
        # Skip if the user is a bot
        if interaction.user.bot:
            return
            
        # Common set of commands that might affect balance
        balance_affecting_commands = {
            "work", "crime", "rob",    # Income
            "roulette", "blackjack",   # Gambling
            "deposit", "withdraw", "donate",  # Banking
            "balance"                  # Check balance
        }
        
        # Special handling for donate command 
        if interaction.command and interaction.command.name == "donate":
            target = await self._extract_donation_target(interaction)
            
            if target and target.id != interaction.user.id:
                await self._process_donation_target(interaction, target)
        
        # Check for any command that might affect balance
        if interaction.command and interaction.command.name in balance_affecting_commands:
            await balance_challenge_manager.trigger_balance_challenge(self.bot, interaction)

    except Exception as e:
        self.debug.log(f"Error in on_app_command_completion: {e}")
        
async def _extract_donation_target(self, interaction):
    """Extract donation target from interaction data."""
    try:
        options = interaction.data.get("options", [])
        for option in options:
            if option.get("name") == "target":
                target_id = option.get("value")
                self.debug.log(f"Found target ID: {target_id}")
                
                # Try to resolve the target using fetch_user first
                target = await self.bot.fetch_user(int(target_id))
                if not target:
                    self.debug.log(f"Failed to fetch user with ID {target_id}")
                    return None
                    
                # Try to resolve as member if possible
                try:
                    member = await interaction.guild.fetch_member(int(target_id))
                    if member:
                        target = member
                except:
                    # Continue with the user object if we can't get the member
                    pass
                    
                self.debug.log(f"Resolved target: {target.display_name if target else 'None'}")
                return target
    except Exception as e:
        self.debug.log(f"Error extracting donation target: {e}")
    
    return None
    
async def _process_donation_target(self, interaction, target):
    """Process a donation target for balance challenge checking."""
    # Avoid checking the same target multiple times simultaneously
    target_id = target.id
    acquire_lock = False
    
    # Use thread-safe locking
    with threading.Lock():
        if target_id in self.donation_check_locks:
            self.debug.log(f"Target {target_id} already being checked, skipping")
            return
        
        # Set lock for this target
        self.donation_check_locks[target_id] = True
        acquire_lock = True
    
    if acquire_lock:
        try:
            # Wait for donation to complete and balances to update
            self.debug.log(f"Waiting for donation to complete...")
            await asyncio.sleep(3.0)
            
            # Check if the target now meets the challenge threshold
            result = await balance_challenge_manager.trigger_challenge_for_donation_target(
                self.bot, interaction.guild, target
            )
            self.debug.log(f"Challenge trigger result for {target.display_name}: {result}")
        finally:
            # Clear the lock regardless of the outcome
            with threading.Lock():
                if target_id in self.donation_check_locks:
                    del self.donation_check_locks[target_id]
```

### 10. Command Cooldown Consistency

**Issue:** Some commands might not properly check cooldowns before execution.

**Files Affected:**
- `work_cmds.py`, `crime_cmds.py`, `rob_cmds.py`
- `balance_challenge.py`
- Other commands with cooldowns

**Fix:**
Implement a centralized cooldown checking method in `EconomyCog` and use it consistently:

```python
# In economy_base.py
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
```

Use this method in all commands with cooldowns:

```python
# In work_cmds.py
@app_commands.command(name="work", description="Work to earn Medals.")
@command_error_handler
async def work(self, interaction: discord.Interaction):
    """Work to earn Medals."""
    # Check prison status
    if not await self.check_prison_status(interaction):
        return
        
    # Check balance challenge status
    if not await self.check_balance_challenge(interaction):
        return
        
    # Handle cooldown with unified method
    if not await self.handle_cooldown(interaction, "work", DEFAULT_WORK_COOLDOWN):
        return
    
    # Rest of command logic...
```

## Implementation Notes

When implementing these fixes:

1. Make the changes incrementally and test each change before moving on to the next.
2. Be mindful of the circular dependencies when modifying imports.
3. Maintain consistent error handling across all commands and UI components.
4. Ensure proper thread safety for all data operations, especially when multiple users might be performing actions simultaneously.
5. Test edge cases thoroughly, particularly for the balance challenge system and prison/escape mechanics.

## Project Structure Reference

Remember that SennaBot uses a modular architecture with the following key components:

- **Athena Framework:** Core services and utilities
- **Cogs:** Command modules organized by functionality
- **UI Components:** Interactive views for complex interactions
- **Data Service:** Central data persistence and caching

Always consider how your changes will affect the interactions between these components.
