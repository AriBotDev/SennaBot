# SennaBot File Structure Documentation

## Overview

This document outlines the architecture for SennaBot, a Discord bot with a modular design focusing on economy simulation, general utility, and extensibility. The architecture is designed to support current functionality while allowing for future expansion with features like a karma system, factions, classes, enhanced injury mechanics, and shop/inventory systems.

## Core Structure

```
SennaBot/
├── athena/                   # Central framework
├── cogs/                     # Command groups
├── config/                   # Configuration files
├── data/                     # Data storage
├── bot.py                    # Main entry point
├── config.py                 # Environment and configuration loading
├── requirements.txt          # Python package dependencies
├── .env                      # Environment file for tokens and other variables
└── sennabot-structure.md     # This File
```

## Athena Framework

The Athena framework serves as the central nervous system of the bot, providing core services used throughout the application.

```
SennaBot/
├── athena/
│   ├── initAthena.py         # Initialization and exports
│   ├── frameworkCore.py      # Core framework functionality
│   ├── loggingManager.py     # Centralized logging system
│   ├── commandHandler.py     # Command registration and whitelist management
│   ├── dataManager.py        # Unified data management interface
│   ├── cacheManager.py       # Cache management for data access optimization
│   ├── concurrencyManager.py # Handles concurrent operations and synchronization
│   ├── eventHandler.py       # Discord event handling
│   ├── viewManager.py        # UI component and game state management
│   └── errorHandler.py       # Global error handling
```

### File Purposes

- **initAthena.py**: Exports framework components and initializes the framework
- **frameworkCore.py**: Provides foundational services like bot initialization, event handling
- **loggingManager.py**: Handles logging to files, console, with different severity levels and contexts
- **commandHandler.py**: Manages command registration, permissions, and whitelist behavior
- **dataManager.py**: Provides a unified interface for data operations with flexible storage backends
- **cacheManager.py**: Implements caching strategies to reduce file I/O and improve performance
- **concurrencyManager.py**: Manages locks and transactions for safe concurrent data access
- **eventHandler.py**: Centralizes Discord event handling (ready, message, guild_join, etc.)
- **viewManager.py**: Manages UI components and game states with persistence across interactions
- **errorHandler.py**: Global error catching, formatting, and reporting with different severity levels

## Configuration

Configuration is separated from code for easier management and adjustments without code changes.

```
SennaBot/
├── config/
│   ├── botConfig.yaml        # Bot-wide settings
│   ├── economyConfig.yaml    # Economy parameters
│   ├── generalConfig.yaml    # General command settings
│   ├── loggingConfig.yaml    # Logging configuration
│   ├── cacheConfig.yaml      # Cache settings and TTL values
│   └── storageConfig.yaml    # Storage backend configuration
```

### File Purposes

- **botConfig.yaml**: Global bot settings like prefix, owner ID, default permissions
- **economyConfig.yaml**: Economy system parameters like payout rates, cooldowns, failure rates
- **generalConfig.yaml**: Settings for general utility commands
- **loggingConfig.yaml**: Logging levels, formats, and destinations
- **cacheConfig.yaml**: Cache time-to-live values, size limits, and invalidation policies
- **storageConfig.yaml**: Storage backend selection and connection parameters

## Cogs Structure

Commands are organized into cogs, which are grouped by functionality.

```
SennaBot/
├── cogs/
│   ├── initCogs.py           # Cog registration
│   ├── baseCog.py            # Base cog with shared functionality
│   ├── general/              # General commands
│   │   ├── initGeneral.py    # General module initialization
│   │   ├── generalBase.py    # Shared general functionality
│   │   ├── utilityCmds.py    # Utility commands (gdtrello, etc.)
│   │   ├── socialCmds.py     # Social commands (headpats, etc.)
│   │   └── generalOwnerCmds.py # Owner-only general commands
│   └── economy/              # Economy system
│       ├── initEconomy.py    # Economy module initialization
│       ├── economyBase.py    # Shared economy functionality
│       ├── common/           # Common economy components
│       │   ├── userManager.py  # User data handling
│       │   ├── responseManager.py # Response formatting/selection
│       │   └── dataFunctions.py # Economy data functions
│       ├── activities/       # Income generating commands
│       │   ├── activitiesBase.py # Base for activity commands
│       │   ├── workCmds.py   # Work commands
│       │   ├── crimeCmds.py  # Crime commands
│       │   └── robCmds.py    # Rob commands
│       ├── banking/          # Banking commands
│       │   ├── bankingBase.py # Base for banking commands
│       │   ├── accountCmds.py # Account management
│       │   └── leaderboardCmds.py # Leaderboard commands
│       ├── games/            # Game commands
│       │   ├── gamesBase.py  # Base for game commands
│       │   ├── gameStates.py # Game state definitions and handlers
│       │   ├── rouletteCmds.py # Roulette game
│       │   ├── blackjackCmds.py # Blackjack game
│       │   └── balanceChallenge.py # Balance challenge
│       ├── prison/           # Prison system
│       │   ├── prisonBase.py # Base for prison commands
│       │   ├── escapeCmds.py # Escape commands
│       │   ├── breakoutViews.py # UI components for breakout games
│       │   └── breakoutCmds.py # Breakout commands
│       ├── health/           # Health system
│       │   ├── healthBase.py # Base for health commands
│       │   └── morticianCmds.py # Mortician commands
│       └── economyOwnerCmds.py # Owner economy commands
```

### Base Cog Functionality

The `baseCog.py` provides functionality shared across all cogs:
- Command registration and metadata
- Permission checking
- Basic messaging and response formatting
- Error handling
- Access to framework services

### General Commands

- **generalBase.py**: Shared functionality for general commands
- **utilityCmds.py**: Utility commands like gdtrello links
- **socialCmds.py**: Social interaction commands like headpats
- **generalOwnerCmds.py**: Owner-only commands for general bot management including server whitelist commands

### Economy System

#### Core Components

- **economyBase.py**: Base class with shared economy functions
- **common/userManager.py**: User data management (balances, cooldowns, etc.)
- **common/responseManager.py**: Handles loading and formatting responses
- **common/dataFunctions.py**: Common data operations for economy

#### Activity Commands

- **activitiesBase.py**: Common functionality for income-generating commands
- **workCmds.py**: Work commands for earning currency
- **crimeCmds.py**: Crime commands for high-risk, high-reward earning
- **robCmds.py**: Rob commands for stealing from other users

#### Banking Commands

- **bankingBase.py**: Shared banking functionality
- **accountCmds.py**: Commands for managing personal accounts 
- **leaderboardCmds.py**: Leaderboard display and management

#### Game Commands

- **gamesBase.py**: Common game functionality
- **gameStates.py**: Defines game state objects and persistence logic
- **rouletteCmds.py**: Roulette gambling game
- **blackjackCmds.py**: Blackjack card game
- **balanceChallenge.py**: Special challenge for wealthy players

#### Prison System

- **prisonBase.py**: Common prison functionality
- **escapeCmds.py**: Prison escape commands
- **breakoutViews.py**: UI views for the various prison breakout minigames
- **breakoutCmds.py**: Commands for breaking others out of prison

#### Health System

- **healthBase.py**: Common health and injury functionality
- **morticianCmds.py**: Medical treatment commands

## Data Storage

User data, responses, and configurations are stored in JSON files.

```
SennaBot/
├── data/
│   ├── responses/            # Response templates
│   │   ├── work.json         # Work command responses
│   │   ├── crime.json        # Crime command responses
│   │   ├── rob.json          # Rob command responses
│   │   ├── death.json        # Death scenario responses
│   │   ├── injury.json       # Injury scenario responses
│   │   └── prison.json       # Prison-related responses
│   ├── serverSaves/          # Server-specific data
│   │   └── [server_id].json  # One file per server
│   ├── gameStates/           # Persistent game state data
│   │   └── [game_id].json    # One file per active game
│   ├── dm_logs/              # DM logs
│   │   └── [username]_[id].txt # One file per user
│   └── whitelist.json        # Server whitelist data
```

### Data Structure

#### User Data (in server_id.json)
```json
{
  "user_id": {
    "username": "Username",
    "pockets": 100,
    "savings": 500,
    "cooldowns": {
      "work": 1612345678,
      "crime": 1612345678,
      "rob": 1612345678,
      "roulette": 1612345678,
      "escape": 1612345678,
      "breakout": 1612345678
    },
    "injured": false,
    "injuries": 0,
    "prison": null,
    "last_robbed": 0,
    "beat_balance_challenge": false
  }
}
```

#### Game State Data (in game_id.json)
```json
{
  "game_type": "blackjack",
  "start_time": 1612345678,
  "guild_id": 123456789,
  "players": [123456789, 987654321],
  "current_player": 123456789,
  "bet": 100,
  "deck": ["AS", "2H", "KD", ...],
  "hands": {
    "123456789": ["AS", "KH"],
    "987654321": ["QS", "2D"]
  },
  "last_activity": 1612345680
}
```

#### Response Data (e.g., work.json)
```json
{
  "work": [
    "You worked and earned {amount} Medals.",
    "Another work response with {amount} Medals."
  ],
  "work_rare_success": [
    "Rare success message with {amount} Medals from original {original} Medals, a {multiplier}x boost!"
  ]
}
```

#### Whitelist Data (whitelist.json)
```json
{
  "guild_id": {
    "server_name": "Server Name",
    "general": true,
    "economy": false
  }
}
```

## Key Components & Interfaces

### Athena Framework

#### dataManager.py Interface
```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def load(self, path: str) -> dict:
        """Load data from the specified path"""
        pass
        
    @abstractmethod
    def save(self, path: str, data: dict) -> None:
        """Save data to the specified path"""
        pass
        
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if data exists at the specified path"""
        pass

class JsonBackend(StorageBackend):
    """JSON file storage backend implementation"""
    # Implementation for JSON file storage

class SqliteBackend(StorageBackend):
    """SQLite database storage backend implementation"""
    # Implementation for SQLite storage

def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend"""
    pass

# Higher-level data access functions
def load_guild_data(guild_id: int) -> dict
def save_guild_data(guild_id: int, data: dict) -> None
def load_game_state(game_id: str) -> dict
def save_game_state(game_id: str, data: dict) -> None
def load_responses(category: str = None) -> dict
def get_response(category: str, key: str, **kwargs) -> str
def load_whitelist() -> dict
def save_whitelist(whitelist: dict) -> None
def ensure_dm_log_directory() -> None
def log_dm(user: discord.User, message: discord.Message) -> None
```

#### cacheManager.py Interface
```python
class Cache:
    """Base cache implementation"""
    
    def get(self, key: str) -> any:
        """Get a value from the cache"""
        pass
        
    def set(self, key: str, value: any, ttl: int = None) -> None:
        """Set a value in the cache with optional TTL"""
        pass
        
    def delete(self, key: str) -> None:
        """Delete a value from the cache"""
        pass
        
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache"""
        pass
        
    def clear(self) -> None:
        """Clear all values from the cache"""
        pass

class CacheManager:
    """Manages different cache instances"""
    
    def __init__(self):
        self.caches = {}
    
    def get_cache(self, name: str) -> Cache:
        """Get or create a named cache instance"""
        pass
        
    def invalidate(self, name: str = None) -> None:
        """Invalidate a named cache or all caches"""
        pass

# Decorators for easy cache usage
def cached(cache_name: str, key_pattern: str, ttl: int = None):
    """Decorator to cache function results"""
    pass

# Cache instances
guild_data_cache = get_cache_manager().get_cache('guild_data')
user_data_cache = get_cache_manager().get_cache('user_data')
response_cache = get_cache_manager().get_cache('responses')
```

#### concurrencyManager.py Interface
```python
class DataLock:
    """Lock for synchronizing data access"""
    
    def __init__(self, key: str):
        self.key = key
    
    async def __aenter__(self):
        """Acquire the lock"""
        pass
        
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Release the lock"""
        pass

class TransactionManager:
    """Manages data transactions with atomic operations"""
    
    async def begin_transaction(self, key: str):
        """Begin a transaction for the given key"""
        pass
        
    async def commit_transaction(self, key: str):
        """Commit the transaction for the given key"""
        pass
        
    async def rollback_transaction(self, key: str):
        """Rollback the transaction for the given key"""
        pass
        
    async def in_transaction(self, key: str, callback, *args, **kwargs):
        """Execute a callback within a transaction"""
        pass

# Decorators for easy concurrency control
def with_lock(key_pattern: str):
    """Decorator to acquire a lock for the function execution"""
    pass
    
def transactional(key_pattern: str):
    """Decorator to execute a function in a transaction"""
    pass

# Lock factory function
def get_lock(key: str) -> DataLock:
    """Get a lock for the specified key"""
    pass
```

#### loggingManager.py Interface
```python
def setup_logging() -> None
def get_logger(name: str) -> logging.Logger
def log_command(ctx_or_interaction, command_name: str, success: bool, error: Exception = None) -> None
def log_guild_change(guild: discord.Guild, action: str) -> None
def log_user_input(guild: discord.Guild, message: str) -> None
def ensure_log_files() -> None
```

#### commandHandler.py Interface
```python
def register_commands(bot, cog, guild_ids: list = None) -> None
def sync_commands(bot) -> None
def reload_commands(bot) -> None
def get_command_category(command_name: str) -> str
def get_general_guilds() -> list
def get_economy_guilds() -> list
def ensure_whitelist_entry(whitelist: dict, guild_id: str, guild_name: str) -> dict

# Command registration decorators
def whitelisted_command(category: str):
    """Decorator to register a command with a whitelist category"""
    def decorator(func):
        func.__whitelist_category__ = category
        return func
    return decorator

def owner_command():
    """Decorator to mark a command as owner-only"""
    def decorator(func):
        func.__owner_only__ = True
        return func
    return decorator

def cooldown_command(cooldown_key: str):
    """Decorator to apply a cooldown to a command"""
    def decorator(func):
        func.__cooldown_key__ = cooldown_key
        return func
    return decorator
```

#### eventHandler.py Interface
```python
def register_events(bot) -> None
def on_ready_handler(bot) -> callable
def on_guild_join_handler(bot) -> callable
def on_guild_remove_handler(bot) -> callable
def on_message_handler(bot) -> callable
def on_interaction_handler(bot) -> callable
def on_command_error_handler(bot) -> callable
def on_app_command_error_handler(bot) -> callable
```

#### viewManager.py Interface
```python
# Base classes for different types of views
class BaseView(discord.ui.View):
    """Base view with common functionality"""
    
class GameView(BaseView):
    """Base view for game interfaces"""
    
    def __init__(self, game_state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_state = game_state
    
    async def persist_state(self):
        """Save the current game state"""
        pass

class PrisonView(BaseView):
    """Base view for prison-related interfaces"""
    
class ConfirmationView(BaseView):
    """Simple confirmation view with yes/no buttons"""

# Game state management
class GameStateManager:
    """Manages game state persistence and lifecycle"""
    
    def create_game(self, game_type: str, guild_id: int, players: list, **kwargs) -> str:
        """Create a new game state and return its ID"""
        pass
        
    def load_game(self, game_id: str) -> dict:
        """Load a game state by ID"""
        pass
        
    def save_game(self, game_id: str, state: dict) -> None:
        """Save a game state"""
        pass
        
    def end_game(self, game_id: str) -> None:
        """End a game and clean up its state"""
        pass
        
    def get_active_games(self, guild_id: int = None, player_id: int = None) -> list:
        """Get active games, optionally filtered by guild or player"""
        pass
        
    def cleanup_stale_games(self, older_than: int = 3600) -> None:
        """Clean up inactive games older than the specified time"""
        pass

# Factory functions for common view types
def create_confirmation_view(callback) -> ConfirmationView
def create_game_view(game_type: str, game_state: dict, **kwargs) -> GameView
def create_prison_view(prison_type: str, **kwargs) -> PrisonView
```

#### errorHandler.py Interface
```python
def setup_error_handlers(bot) -> None
def handle_command_error(ctx, error) -> None
def handle_app_command_error(interaction, error) -> None
def format_error(error) -> str
def report_critical_error(error, context) -> None
def is_expected_error(error) -> bool
```

### Economy Components

#### userManager.py Interface
```python
def default_user_data(user: discord.User) -> dict
def get_user_data(guild_id: int, user) -> dict
def get_pockets(guild_id: int, user) -> int
def update_pockets(guild_id: int, user, amount: int) -> None
def get_savings(guild_id: int, user) -> int
def update_savings(guild_id: int, user, amount: int) -> None
def set_cooldown(guild_id: int, user, command: str) -> None
def check_cooldown(guild_id: int, user, command: str, cooldown: int) -> tuple[bool, int]
def total_funds(guild_id: int, user) -> int
def get_injury_status(guild_id: int, user) -> dict
def add_injury(guild_id: int, user) -> int
def heal_injuries(guild_id: int, user) -> None
def set_last_robbed(guild_id: int, user) -> None
def check_last_robbed(guild_id: int, user, cooldown: int = 600) -> tuple[bool, int]
def is_in_challenge(user_id: int) -> bool
def add_to_challenge(user_id: int, guild_id: int) -> None
def remove_from_challenge(user_id: int) -> None
```

#### responseManager.py Interface
```python
def load_responses(category: str = None) -> dict
def get_response_category(key: str) -> str
def get_response(key: str, **kwargs) -> str
def format_response(template: str, **kwargs) -> str
```

#### economyBase.py Interface
```python
class EconomyBase(commands.Cog):
    def __init__(self, bot)
    def get_response(self, key: str, **kwargs) -> str
    async def prison_check(self, interaction) -> bool
    async def challenge_check(self, interaction) -> bool
    async def send_embed(self, interaction, title, description, color, ephemeral=False, extra_mentions=[]) -> None
    def get_app_commands(self) -> list
    async def cog_app_command_check(self, interaction) -> bool
```

### Prison System Components

#### prisonBase.py Interface
```python
def select_prison_tier() -> tuple
def get_prison_tier_data(tier_name: str) -> dict
def calculate_release_time(tier_name: str) -> int
def incarcerate_user(guild_id: int, user, tier_name: str, duration: int = None) -> None
def release_user(guild_id: int, user) -> bool
def is_in_prison(guild_id: int, user) -> bool
def get_prison_info(guild_id: int, user) -> dict
def get_escape_chance(guild_id: int, user, tier_name: str) -> int
```

#### breakoutViews.py Interface
```python
class OfficerGroupBreakoutView(discord.ui.View):
    """View for Officer Group breakout minigame"""
    
class OldGuardsBreakoutView(discord.ui.View):
    """View for Old Guards breakout minigame"""
    
class SoldatBrigadeBreakoutView(discord.ui.View):
    """View for Soldat Brigade breakout minigame"""
    
class LancerLegionBreakoutView(discord.ui.View):
    """View for Lancer Legion breakout minigame"""
    
class RookDivisionBreakoutView(discord.ui.View):
    """View for Rook Division breakout minigame"""
    
class MorticianWingBreakoutView(discord.ui.View):
    """View for Mortician Wing breakout minigame"""
    
class JaegerPathBreakoutView(discord.ui.View):
    """View for Jaeger Camp breakout minigame"""
    
class JaegerBoxesBreakoutView(discord.ui.View):
    """View for Jaeger Camp boxes minigame"""
    
class EscapeJaegerView(discord.ui.View):
    """View for Jaeger Camp escape minigame"""
```

## Component Interactions

### Command Execution Flow
1. User enters a command
2. `bot.py` receives the command and routes to appropriate cog
3. commandHandler.py checks guild whitelist permissions
4. Cog's `cog_app_command_check` checks prerequisites (prison status, challenge status)
5. Command acquires necessary locks via concurrencyManager.py for thread safety
6. Command checks cache for data via cacheManager.py before loading from storage
7. Cog executes command logic, accessing data via `dataManager.py`
8. If interactive UI is needed, a View is created via viewManager.py
9. For games, game state is tracked and persisted via GameStateManager
10. Results are cached, saved to storage, and response is sent to user

### Data Flow with Concurrency and Caching
1. Command attempts to get data from cache first
2. If cache miss, acquire lock for the resource
3. Load data from storage backend via `dataManager.py`
4. Store loaded data in cache
5. Perform operations within a transaction if needed
6. Save modified data back to storage and update cache
7. Release lock

### Response Flow
1. Command determines which response template to use
2. Check cache for the response template
3. If cache miss, load template from storage
4. Template is randomly selected from available options
5. Template is filled with data specific to the interaction
6. Formatted response is sent to the user

### Error Flow
1. Command or event handler encounters an error
2. Local try/except blocks handle expected errors
3. Unhandled errors bubble up to global error handlers
4. errorHandler.py formats and logs the error
5. User receives appropriate error message
6. Critical errors are reported to bot owner

## Event Handling

### Key Discord Events
1. **on_ready**: Initialize services, process prison releases, sync commands
2. **on_guild_join**: Add to whitelist, register commands, log join
3. **on_guild_remove**: Update logs, clean up
4. **on_message**: Check for DMs to log, process headpats responses
5. **on_interaction**: Process prison status changes, log interactions
6. **on_command_error** / **on_app_command_error**: Handle command errors

## Implementation Guidelines

### Base Principles
1. **Single Responsibility**: Each component should have a single responsibility
2. **DRY (Don't Repeat Yourself)**: Common functionality should be extracted to base classes or utility modules
3. **Configuration Over Code**: Prefer configuration in YAML files over hardcoded values
4. **Progressive Enhancement**: Core functionality should work even if advanced features fail
5. **Defensive Programming**: Validate inputs, handle edge cases, fail gracefully
6. **Thread Safety**: Use locks and transactions for concurrent data access
7. **Performance First**: Use caching and optimized storage access patterns

### Code Organization
- Commands should focus on interaction logic
- Business logic should be in separate utility modules
- Data access should be through the data manager using appropriate caching
- Configuration should be in YAML files, not in code
- UI components should be in separate view classes
- Game state should be properly persisted and managed

### Naming Conventions
- Files: snake_case for modules, PascalCase for class-only modules
- Classes: PascalCase
- Methods/Functions: snake_case
- Constants: UPPER_SNAKE_CASE
- Private methods/variables: _snake_case (with leading underscore)

### Error Handling
- Commands should use try/except and provide user-friendly errors
- Unexpected errors should be logged via loggingManager.py
- Critical errors should be reported to the bot owner
- Always clean up resources (close files, end tasks) in finally blocks
- Roll back transactions on error

### Testing Approach
- Unit tests for utility functions and isolated logic
- Integration tests for command flows
- Mocked Discord API for testing without real Discord
- Separate test configuration from production

### Dependency Management
- All dependencies listed in requirements.txt
- Version pinning for stability
- Minimal dependency footprint to reduce conflicts

### Concurrency Patterns
- Use locks for mutating operations on shared data
- Use read-write locks where appropriate to allow concurrent reads
- Keep lock scope as narrow as possible
- Use transactions for operations that need to be atomic
- Always release locks in finally blocks

### Caching Strategy
- Cache frequently accessed, rarely changing data
- Use appropriate TTL values for different types of data
- Invalidate cache when underlying data changes
- Use cache versioning for complex invalidation scenarios
- Gracefully handle cache misses
