# SennaBot Debug Guide

This document identifies potential issues in SennaBot's codebase and provides guidance on how to fix them. Use this as a reference when improving the bot's stability and performance.

## Core Bot Architecture

### Error Handling in Event Handlers

**Issue:** In `bot.py`, event handlers like `on_message`, `on_guild_join`, and `on_ready` have minimal error handling.

**Files Affected:**
- `bot.py` - Lines 87-125 (event handlers)

**Fix:**
```python
@bot.event
async def on_guild_join(guild):
    """Called when the bot joins a new guild."""
    try:
        logger.info(f"Bot added to guild: {guild.name} (ID: {guild.id})")
        debug.log(f"Bot added to guild: {guild.name} (ID: {guild.id})")
        
        # Create permission entry for this guild
        PermissionManager.ensure_guild_entry(
            PermissionManager.load_permissions(),
            str(guild.id),
            guild.name
        )
        PermissionManager.save_permissions()
        
        # Sync commands for this guild
        guild_permissions = PermissionManager.get_guild_permissions(guild.id)
        await CommandRegistry.sync_guild_commands(bot, guild.id, guild_permissions)
    except Exception as e:
        logger.error(f"Error in on_guild_join event: {e}")
        ErrorHandler.handle_event_error("on_guild_join", e, {"guild_id": guild.id, "guild_name": guild.name})
```

Apply similar try-except blocks to all event handlers.

### Command Extraction Inconsistency

**Issue:** In `cmd_registry.py`, the `_extract_guild_commands` method uses multiple approaches to extract commands, which could become inconsistent.

**Files Affected:**
- `cmd_registry.py` - Lines 120-160 (command extraction)

**Fix:**
Standardize on a single, reliable method:

```python
@classmethod
def _extract_guild_commands(cls, bot: commands.Bot, cog_instance: commands.Cog) -> List[app_commands.Command]:
    """Extract app commands from a cog instance using standard attributes."""
    commands_list = []
    cog_name = cog_instance.__class__.__name__
    
    # Primary method: Use get_app_commands if available
    if hasattr(cog_instance, 'get_app_commands') and callable(getattr(cog_instance, 'get_app_commands')):
        try:
            commands_list = cog_instance.get_app_commands() or []
            debug.log(f"Extracted {len(commands_list)} commands via get_app_commands from {cog_name}")
            return commands_list
        except Exception as e:
            debug.log(f"Error extracting commands via get_app_commands from {cog_name}: {e}")
    
    # Fallback: Check for app_command attributes only if primary method failed
    try:
        for name, method in inspect.getmembers(cog_instance, predicate=inspect.ismethod):
            if hasattr(method, 'app_command') and method.app_command not in commands_list:
                commands_list.append(method.app_command)
    except Exception as e:
        debug.log(f"Error extracting commands from methods in {cog_name}: {e}")
    
    debug.log(f"Total of {len(commands_list)} commands extracted from cog {cog_name}")
    return commands_list
```

### Command Syncing Cleanup

**Issue:** When syncing commands, old commands might not be properly removed if they're no longer registered.

**Files Affected:**
- `cmd_registry.py` - Lines 170-215 (sync_guild_commands)

**Fix:**
Add code to track and clean up old commands:

```python
@classmethod
async def sync_guild_commands(cls, bot: commands.Bot, guild_id: int, permissions: Dict[str, bool]) -> bool:
    """Sync commands for a specific guild based on permissions."""
    guild_id_str = str(guild_id)
    guild_obj = discord.Object(id=guild_id)
    debug.log(f"Syncing commands for guild {guild_id}")
    
    try:
        # Get previously registered commands for this guild
        old_commands = {}
        if guild_id_str in cls._registered_commands:
            for category, cmd_list in cls._registered_commands[guild_id_str].items():
                for cmd_name in cmd_list:
                    old_commands[cmd_name] = category
        
        # Clear existing guild commands
        bot.tree.clear_commands(guild=guild_obj)
        debug.log(f"Cleared commands for guild {guild_id}")
        
        # Initialize tracking for this guild
        if guild_id_str not in cls._registered_commands:
            cls._registered_commands[guild_id_str] = {}
        else:
            # Clear the old registered commands for this guild
            cls._registered_commands[guild_id_str] = {}
        
        # Register commands based on permissions
        for category, enabled in permissions.items():
            if enabled:
                if category not in cls._registered_commands[guild_id_str]:
                    cls._registered_commands[guild_id_str][category] = []
                
                # Get all cogs of this category
                category_cogs = [
                    cog for cog in bot.cogs.values()
                    if any(isinstance(cog, cog_class) for cog_class in cls.get_category_cogs(category))
                ]
                
                # Extract and register commands from cogs
                for cog in category_cogs:
                    cog_commands = cls._extract_guild_commands(bot, cog)
                    for command in cog_commands:
                        bot.tree.add_command(command, guild=guild_obj)
                        cls._registered_commands[guild_id_str].setdefault(category, []).append(command.name)
                        if command.name in old_commands:
                            del old_commands[command.name]  # Remove from old commands as it's still valid
                        debug.log(f"Added command {command.name} to guild {guild_id}")
        
        # Log any commands that were removed
        if old_commands:
            debug.log(f"Removed old commands from guild {guild_id}: {', '.join(old_commands.keys())}")
        
        # Sync the command tree for this guild
        await bot.tree.sync(guild=guild_obj)
        debug.log(f"Synced command tree for guild {guild_id}")
        
        # Log summary of registered commands
        for category, commands_list in cls._registered_commands[guild_id_str].items():
            debug.log(f"Guild {guild_id} has {len(commands_list)} {category} commands")
        
        return True
    
    except Exception as e:
        debug.log(f"Error syncing commands for guild {guild_id}: {e}")
        return False
```

## Economy System

### Negative Balance Handling

**Issue:** Some economy operations don't properly handle negative balances.

**Files Affected:**
- `account_cmds.py` - Lines 150-180 (withdraw function)
- `account_cmds.py` - Lines 190-230 (donate function)
- `economy_base.py` - Lines 90-140 (update_pockets, update_savings)

**Fix:**
Add more robust balance checking in `economy_base.py`:

```python
def update_pockets(self, guild_id, user, amount):
    """Update a user's pocket balance with validation."""
    user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
    current_balance = user_data.get("pockets", 0)
    
    # For withdrawals, ensure sufficient funds
    if amount < 0 and abs(amount) > current_balance and not self.allow_negative_pockets:
        self.debug.log(f"Attempted to withdraw {abs(amount)} from pockets with balance {current_balance}")
        return current_balance  # Return unchanged balance
        
    user_data["pockets"] = current_balance + amount
    guild_data = DataService.load_guild_data(guild_id)
    guild_data[str(user.id)] = user_data
    DataService.save_guild_data(guild_id, guild_data)
    return user_data["pockets"]
```

Also, update `withdraw` and `donate` commands to check balances before operations.

### Race Conditions in Transactions

**Issue:** Multiple concurrent transactions could lead to race conditions where balance changes are lost.

**Files Affected:**
- `data_service.py` - Lines 195-230 (save_guild_data, load_guild_data)
- `economy_base.py` - Lines 90-140 (update_pockets, update_savings)

**Fix:**
Implement a simple lock mechanism in DataService:

```python
# In data_service.py
import threading

class DataService:
    # Add locks dictionary
    _guild_locks = {}
    
    @classmethod
    def get_guild_lock(cls, guild_id):
        """Get or create a lock for a specific guild."""
        guild_id = str(guild_id)
        if guild_id not in cls._guild_locks:
            cls._guild_locks[guild_id] = threading.Lock()
        return cls._guild_locks[guild_id]
    
    @classmethod
    def load_guild_data(cls, guild_id):
        """Load data for a specific guild with locking."""
        guild_id = str(guild_id)
        debug.log(f"Loading guild data for {guild_id}")
        
        # Acquire lock for this guild
        with cls.get_guild_lock(guild_id):
            # Return cached data if available
            if guild_id in cls._guild_cache:
                debug.log(f"Using cached data for guild {guild_id}")
                return cls._guild_cache[guild_id]
            
            # Load from file
            file_path = os.path.join(cls.GUILDS_DIR, f"{guild_id}.json")
            data = cls._safe_load_json(file_path, {})
            
            # Cache and return data
            cls._guild_cache[guild_id] = data
            return data
    
    @classmethod
    def save_guild_data(cls, guild_id, data):
        """Save data for a specific guild with locking."""
        guild_id = str(guild_id)
        debug.log(f"Saving guild data for {guild_id}")
        
        # Acquire lock for this guild
        with cls.get_guild_lock(guild_id):
            # Update cache
            cls._guild_cache[guild_id] = data
            
            # Save to file
            file_path = os.path.join(cls.GUILDS_DIR, f"{guild_id}.json")
            return cls._safe_save_json(file_path, data)
```

Then modify transaction methods to use this locking mechanism.

### Success/Failure Calculations Using Separate Constants

**Issue:** Success/failure rate calculations use constants scattered across files.

**Files Affected:**
- `crime_cmds.py` - Lines 25-35 (CRIME_FAIL_RATE, CRIME_DEATH_CHANCE, etc.)
- `rob_cmds.py` - Lines 20-30 (ROB_FAIL_RATE, ROB_DEATH_CHANCE, etc.)
- `injury_system.py` - Lines 20-60 (FAIL_RATES, get_fail_rate, etc.)

**Fix:**
Consolidate constants in a central location (injury_system.py) and reference them:

```python
# In injury_system.py
# Base failure rates for activities
FAIL_RATES = {
    "crime": 51,
    "rob": 55
}

# Outcome probabilities
OUTCOME_CHANCES = {
    "death": 15,    # 15% chance for death on failure
    "injury": 65,   # 65% chance for injury on failure
    "prison": 20    # 20% chance for prison on failure (remainder)
}

# Death penalty
DEATH_SAVINGS_PENALTY = 0.10  # 10% of savings

# Then update all activities to use these consolidated constants
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
```

### Duplicated Cooldown Logic

**Issue:** Cooldown checking and setting code is duplicated across activity commands.

**Files Affected:**
- `economy_base.py` - Lines 145-180 (cooldown methods)
- `work_cmds.py`, `crime_cmds.py`, `rob_cmds.py` - Cooldown sections in commands

**Fix:**
Create a unified cooldown handler method in EconomyCog:

```python
# In economy_base.py
async def handle_cooldown(self, interaction, command_name, cooldown_time, ephemeral=True):
    """
    Unified cooldown handler that checks and sets cooldowns.
    Returns True if command can proceed, False if on cooldown.
    """
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
```

Then use this in activity commands:

```python
@app_commands.command(name="work", description="Work to earn Medals.")
async def work(self, interaction: discord.Interaction):
    """Work to earn Medals."""
    # Check prison status
    if not await self.check_prison_status(interaction):
        return
        
    # Check balance challenge
    if not await self.check_balance_challenge(interaction):
        return
        
    # Handle cooldown with unified method
    if not await self.handle_cooldown(interaction, "work", DEFAULT_WORK_COOLDOWN):
        return
    
    # Rest of command logic...
```

## UI Components

### Timeout Resource Cleanup

**Issue:** UI component timeouts might not consistently clean up resources.

**Files Affected:**
- `breakout_components.py`, `jaeger_components.py` - on_timeout methods
- `blackjack_game.py` - Lines 780-820 (on_timeout method)

**Fix:**
Implement a consistent pattern for timeouts:

```python
async def on_timeout(self):
    """Handle timeout of the component."""
    try:
        # 1. Clean up any game state or resources
        if hasattr(self, 'game_state'):
            # Clean up game state
            pass
            
        # 2. Remove from active games if applicable
        if hasattr(self, 'game_id') and self.game_id in ACTIVE_GAMES:
            del ACTIVE_GAMES[self.game_id]
            
        # 3. Try to update the original message
        if self.message:
            try:
                await self.message.edit(
                    content="This interaction has expired.",
                    view=None  # Remove the view
                )
            except discord.NotFound:
                # Message may have been deleted
                pass
            except discord.HTTPException as e:
                debug.log(f"Error updating message on timeout: {e}")
                
    except Exception as e:
        debug.log(f"Error in timeout handler: {e}")
```

Apply this pattern across all UI components.

### Healing Costs Without Sufficient Funds

**Issue:** The mortician healing command doesn't handle cases where players have insufficient funds.

**Files Affected:**
- `mortician_cmds.py` - Lines 45-90 (see_mortician command)

**Fix:**
Improve the fund check:

```python
@app_commands.command(name="see_mortician", description="Visit the Mortician's Wing to heal your injuries.")
async def see_mortician(self, interaction: discord.Interaction):
    """Visit the mortician to heal injuries."""
    # Check if user is in prison
    # [existing code]
            
    # Get injury status
    from .injury_system import get_injury_status
    injury_status = get_injury_status(interaction.guild.id, interaction.user)
    injuries = injury_status["injuries"]
    
    if injuries <= 0:
        return await self.send_embed(
            interaction, 
            "Mortician's Wing",
            "You are not injured. Did you just come here to steal my stims???",
            discord.Color.orange(), 
            ephemeral=True
        )
            
    heal_cost = injury_status["heal_cost"]
    
    # Check if user has enough funds
    pockets = DataService.get_pockets(interaction.guild.id, interaction.user)
    savings = DataService.get_savings(interaction.guild.id, interaction.user)
    total_funds = pockets + savings
    
    if total_funds < heal_cost:
        return await self.send_embed(
            interaction, 
            "Mortician's Wing",
            f"You need **{heal_cost}** Medals to heal your {injury_status['tier']}. You only have **{total_funds}** Medals total.",
            discord.Color.red(), 
            ephemeral=True
        )
    
    # Handle negative pocket balance
    if pockets < 0:
        return await self.send_embed(
            interaction, 
            "Error",
            "You have a negative pocket balance. Resolve your debt before healing.",
            discord.Color.red(), 
            ephemeral=True
        )
    
    # Take money, favoring pockets first
    # [existing code]
```

### Blackjack Game State Management

**Issue:** Blackjack game has complex state that might not be properly handled.

**Files Affected:**
- `blackjack_game.py` - The entire game implementation

**Fix:**
Add a proper cleanup method and ensure all game paths terminate correctly:

```python
# In BlackjackGameView class
def register_game(self):
    """Register this game in active games tracking."""
    player_key = f"{self.game.initiator.id}-{self.channel.guild.id}"
    opponent_key = f"{self.game.opponent.id}-{self.channel.guild.id}"
    ACTIVE_GAMES[player_key] = self.game
    ACTIVE_GAMES[opponent_key] = self.game

def unregister_game(self):
    """Remove this game from active games tracking."""
    try:
        player_key = f"{self.game.initiator.id}-{self.channel.guild.id}"
        opponent_key = f"{self.game.opponent.id}-{self.channel.guild.id}"
        if player_key in ACTIVE_GAMES:
            del ACTIVE_GAMES[player_key]
        if opponent_key in ACTIVE_GAMES:
            del ACTIVE_GAMES[opponent_key]
    except Exception as e:
        debug.log(f"Error unregistering game: {e}")

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
            except:
                pass
    except Exception as e:
        debug.log(f"Error in game cleanup: {e}")
```

Then call this cleanup method from all game termination paths.

### Game State Cleanup on Interruption

**Issue:** Game state might not be properly cleaned up if interrupted.

**Files Affected:**
- `balance_challenge.py` - ChallengeGame class
- `blackjack_game.py` - BlackjackGameView class

**Fix:**
Register active games with a cleanup handler:

```python
# In balance_challenge.py
# Maintain a dict of active challenges
_active_challenges = {}

def register_challenge(user_id, guild_id, challenge_instance):
    """Register an active challenge."""
    key = f"{user_id}-{guild_id}"
    _active_challenges[key] = challenge_instance
    debug.log(f"Registered challenge for {user_id} in guild {guild_id}")

def unregister_challenge(user_id, guild_id):
    """Unregister an active challenge."""
    key = f"{user_id}-{guild_id}"
    if key in _active_challenges:
        del _active_challenges[key]
        debug.log(f"Unregistered challenge for {user_id} in guild {guild_id}")

def cleanup_abandoned_challenges():
    """Check for and clean up any abandoned challenges."""
    current_time = time.time()
    to_remove = []
    
    for key, challenge in _active_challenges.items():
        if hasattr(challenge, 'last_activity') and (current_time - challenge.last_activity) > 300:  # 5 minutes
            to_remove.append(key)
            try:
                # Try to clean up the challenge
                asyncio.create_task(challenge.handle_timeout())
            except:
                pass
    
    for key in to_remove:
        del _active_challenges[key]
        debug.log(f"Cleaned up abandoned challenge: {key}")
```

Then add a periodic task in the bot to run this cleanup.

## Framework Components

### File Locking for Concurrent Writes

**Issue:** The data service lacks proper file locking for concurrent writes.

**Files Affected:**
- `data_service.py` - Lines 75-120 (_safe_save_json method)

**Fix:**
Implement file locking for atomic writes:

```python
import fcntl

@classmethod
def _safe_save_json(cls, file_path, data):
    """Safely save data to a JSON file with proper locking."""
    cls._ensure_directories()
    debug.start_timer(f"save_json_{os.path.basename(file_path)}")
    
    # Create backup of existing file
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        try:
            shutil.copy2(file_path, backup_path)
            debug.log(f"Created backup at {backup_path}")
        except Exception as e:
            debug.log(f"Error creating backup: {e}")
    
    # Write to temporary file first
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            # Add exclusive file lock
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=4)
            # Release lock (happens automatically when file closed)
            fcntl.flock(f, fcntl.LOCK_UN)
        
        # Rename temp file to actual file (atomic operation)
        os.replace(temp_path, file_path)
        debug.log(f"Successfully saved data to {file_path}")
        return True
        
    except Exception as e:
        debug.log(f"Error saving to {file_path}: {e}")
        return False
        
    finally:
        # Clean up temp file if it still exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        debug.end_timer(f"save_json_{os.path.basename(file_path)}")
```

### Cache Invalidation

**Issue:** Cache management could lead to stale data.

**Files Affected:**
- `data_service.py` - Cache handling throughout
- `perm_manager.py` - Permission caching

**Fix:**
Add proper cache invalidation and TTL:

```python
# In data_service.py
# Add cache TTL
_cache_timestamps = {}
CACHE_TTL = 300  # 5 minutes

@classmethod
def load_guild_data(cls, guild_id, force_reload=False):
    """Load data for a specific guild with TTL caching."""
    guild_id = str(guild_id)
    debug.log(f"Loading guild data for {guild_id}")
    
    current_time = time.time()
    
    # Check if cache is valid
    cache_valid = (
        guild_id in cls._guild_cache and
        guild_id in cls._cache_timestamps and
        current_time - cls._cache_timestamps[guild_id] < CACHE_TTL and
        not force_reload
    )
    
    if cache_valid:
        debug.log(f"Using cached data for guild {guild_id}")
        return cls._guild_cache[guild_id]
    
    # Load from file
    file_path = os.path.join(cls.GUILDS_DIR, f"{guild_id}.json")
    data = cls._safe_load_json(file_path, {})
    
    # Update cache and timestamp
    cls._guild_cache[guild_id] = data
    cls._cache_timestamps[guild_id] = current_time
    
    return data

@classmethod
def invalidate_cache(cls, guild_id=None):
    """Invalidate cache for a specific guild or all guilds."""
    if guild_id:
        guild_id = str(guild_id)
        if guild_id in cls._guild_cache:
            del cls._guild_cache[guild_id]
            if guild_id in cls._cache_timestamps:
                del cls._cache_timestamps[guild_id]
            debug.log(f"Invalidated cache for guild {guild_id}")
    else:
        cls._guild_cache.clear()
        cls._cache_timestamps.clear()
        debug.log("Invalidated all data caches")
```

Apply similar logic to other caching components.

### Permission Check Consistency

**Issue:** Permission checks might not be consistent across all commands.

**Files Affected:**
- Various cog files implementing `cog_app_command_check`

**Fix:**
Standardize the permission check method in BotCog:

```python
# In cog_base.py
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

# Then in subclasses
async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
    """Check permissions for commands in this cog."""
    # Check standard permissions
    if not await self.check_permissions(interaction, "economy"):
        return False
        
    # Additional cog-specific checks...
    return True
```

### Error Reporting to Owner

**Issue:** Error reporting to owner may fail silently.

**Files Affected:**
- `error_handler.py` - Lines 150-180 (_send_error_to_owner method)

**Fix:**
Enhance error reporting with better error handling and logging:

```python
@classmethod
async def _send_error_to_owner(cls, bot, error_report):
    """Send error report to owner with retry and logging."""
    if not cls._owner_id:
        print("No owner ID set for error reporting")
        return False
        
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            owner = await bot.fetch_user(cls._owner_id)
            if not owner:
                print(f"Could not find owner with ID {cls._owner_id}")
                return False
                
            await owner.send(error_report)
            print(f"Error report sent to owner: {error_report[:50]}...")
            return True
            
        except discord.HTTPException as e:
            print(f"HTTP error sending to owner (retry {retry_count+1}/{max_retries}): {e}")
            retry_count += 1
            await asyncio.sleep(1)  # Wait before retry
            
        except Exception as e:
            print(f"Unexpected error sending to owner: {e}")
            return False
    
    print(f"Failed to send error to owner after {max_retries} attempts")
    return False
```

### Error Recovery Paths

**Issue:** Error recovery paths might not be consistent across commands.

**Files Affected:**
- Various command implementations

**Fix:**
Implement a standardized error handling decorator:

```python
# In error_handler.py
def command_error_handler(func):
    """Decorator for standardized command error handling."""
    @functools.wraps(func)
    async def wrapper(self, interaction, *args, **kwargs):
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            # Get command name
            command_name = func.__name__
            
            # Log the error
            self.debug.log(f"Error in {command_name}: {e}")
            
            try:
                # Send error message to user
                if hasattr(self, 'send_embed'):
                    await self.send_embed(
                        interaction,
                        "Error",
                        "An error occurred while processing this command. The bot owner has been notified.",
                        discord.Color.red(),
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "An error occurred while processing this command.",
                        ephemeral=True
                    )
            except:
                # If response failed, try followup
                try:
                    await interaction.followup.send(
                        "An error occurred while processing this command.",
                        ephemeral=True
                    )
                except:
                    pass
            
            # Report to owner if serious
            ErrorHandler.handle_command_error(interaction, e)
            
            # Rethrow specific exceptions we want to bubble up
            if isinstance(e, (commands.CommandNotFound, commands.MissingRequiredArgument)):
                raise
    
    return wrapper
```

Then use this decorator on command methods:

```python
@app_commands.command(name="work", description="Work to earn Medals.")
@command_error_handler
async def work(self, interaction: discord.Interaction):
    """Work to earn Medals."""
    # Command implementation...
```

## Additional Recommendations

1. **Add Unit Tests**: Create unit tests for critical components like the economy system, permission checks, and data persistence.

2. **Performance Monitoring**: Add metrics collection to identify bottlenecks (like slow commands or data operations).

3. **Documentation**: Add more comprehensive documentation, especially for the more complex systems like prison breakouts.

4. **Configuration Management**: Move more hardcoded values to configuration files for easier adjustment.

5. **Database Migration**: Consider migrating to a proper database (like SQLite) for larger deployments.

## Conclusion

This guide covers the main issues identified in the SennaBot codebase. By addressing these concerns, you'll significantly improve the stability, maintainability, and reliability of the bot. Focus on the critical issues first, particularly those related to data integrity and error handling.
