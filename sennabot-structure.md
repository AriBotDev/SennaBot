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
│   ├── commandHandler.py     # Command registration and whitelist management to ensure only certain guilds that have been whitelisted for certain slash commands can only see the slash commands that have been granted whitelist to them
│   ├── dataManager.py        # Unified data management interface
│   └── errorHandler.py       # Global error handling
```

### File Purposes

- **initAthena.py**: Exports framework components and initializes the framework
- **frameworkCore.py**: Provides foundational services like bot initialization, event handling
- **loggingManager.py**: Handles logging to files, console, with different severity levels and contexts
- **commandHandler.py**: Manages command registration, permissions, and whitelist behavior
- **dataManager.py**: Provides a unified interface for data operations across the bot
- **errorHandler.py**: Global error catching, formatting, and reporting

## Configuration

Configuration is separated from code for easier management and adjustments without code changes.

```
SennaBot/
├── config/
│   ├── botConfig.yaml        # Bot-wide settings
│   ├── economyConfig.yaml    # Economy parameters
│   └── generalConfig.yaml    # General command settings
```

### File Purposes

- **botConfig.yaml**: Global bot settings like prefix, owner ID, default permissions
- **economyConfig.yaml**: Economy system parameters like payout rates, cooldowns, failure rates
- **generalConfig.yaml**: Settings for general utility commands

## Cogs Structure

Commands are organized into cogs, which are grouped by functionality.

```
SennaBot/
├── cogs/
│   ├── initCogs.py           # Cog registration
│   ├── baseCog.py            # Base cog with shared functionality
│   ├── general/              # General commands
│   │   ├── initGeneral.py       # General module initialization
│   │   ├── generalBase.py    # Shared general functionality
│   │   ├── utilityCmds.py    # Utility commands (gdtrello, etc.)
│   │   ├── socialCmds.py     # Social commands (headpats, etc.)
│   │   └── generalOwnerCmds.py      # Owner-only general commands
│   └── economy/              # Economy system
│       ├── initEconomy.py       # Economy module initialization
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
│       │   ├── rouletteCmds.py # Roulette game
│       │   ├── blackjackCmds.py # Blackjack game
│       │   └── balanceChallenge.py # Balance challenge
│       ├── prison/           # Prison system
│       │   ├── prisonBase.py # Base for prison commands
│       │   ├── escapeCmds.py # Escape commands
│       │   └── breakoutCmds.py # Breakout commands
│       ├── health/           # Health system
│       │   ├── healthBase.py # Base for health commands
│       │   └── morticianCmds.py # Mortician commands
│       └── economyOwnerCmds.py      # Owner economy commands
```

### Base Cog Functionality

The `baseCog.py` provides functionality shared across all cogs:
- Command registration and metadata
- Permission checking
- Basic messaging and response formatting
- Error handling

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
- **rouletteCmds.py**: Roulette gambling game
- **blackjackCmds.py**: Blackjack card game
- **balanceChallenge.py**: Special challenge for wealthy players

#### Prison System

- **prisonBase.py**: Common prison functionality
- **escapeCmds.py**: Prison escape commands
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
│   ├── serverSaves/              # Server-specific data
│   │   └── [server_id].json  # One file per server
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
      "crime": 1612345678
    },
    "injured": false,
    "injuries": 0,
    "prison": null
  }
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
    "Rare success message with {amount} Medals."
  ]
}
```

## Key Components & Interfaces

### Athena Framework

#### dataManager.py Interface
```python
def load_guild_data(guild_id: int) -> dict
def save_guild_data(guild_id: int, data: dict) -> None
def load_responses(category: str) -> dict
def get_response(category: str, key: str, **kwargs) -> str
def load_whitelist() -> dict
def save_whitelist(whitelist: dict) -> None
```

#### commandHandler.py Interface
```python
def register_commands(bot, cog, guild_ids: list = None) -> None
def sync_commands(bot) -> None
def reload_commands(bot) -> None
```

### Economy Components

#### userManager.py Interface
```python
def get_user_data(guild_id: int, user) -> dict
def update_pockets(guild_id: int, user, amount: int) -> None
def update_savings(guild_id: int, user, amount: int) -> None
def set_cooldown(guild_id: int, user, command: str) -> None
def check_cooldown(guild_id: int, user, command: str, cooldown: int) -> tuple[bool, int]
def get_injury_status(guild_id: int, user) -> dict
def add_injury(guild_id: int, user) -> int
def heal_injuries(guild_id: int, user) -> None
```

#### economyBase.py Interface
```python
class EconomyBase(commands.Cog):
    def __init__(self, bot)
    def get_response(self, key: str, **kwargs) -> str
    async def prison_check(self, interaction) -> bool
    async def challenge_check(self, interaction) -> bool
    async def send_embed(self, interaction, title, description, color) -> None
```

## Component Interactions

### Command Execution Flow
1. User enters a command
2. `bot.py` receives the command and routes to appropriate cog
3. Cog checks guild whitelist permissions and prerequisites 
4. Cog executes command logic, accessing data via `dataManager.py`
5. Results are saved and response is sent to user

### Data Flow
1. User data is loaded from JSON via `dataManager.py`
2. Operations performed by cog commands modify data
3. Modified data is saved back to JSON via `dataManager.py`

### Response Flow
1. Command determines which response template to use
2. `responseManager.py` loads the appropriate template
3. Template is filled with data specific to the interaction
4. Formatted response is sent to the user

## Implementation Guidelines

### Base Principle
Each component should have a single responsibility, and common functionality should be extracted to base classes or utility modules.

### Code Organization
- Commands should focus on interaction logic
- Business logic should be in separate utility modules
- Data access should be through the data manager
- Configuration should be in YAML files, not in code

### Naming Conventions
- Files: PascalCase for base classes, camelCase for modules
- Classes: PascalCase
- Methods/Functions: snake_case
- Constants: UPPER_SNAKE_CASE

### Error Handling
- Commands should use try/except and provide user-friendly errors
- Unexpected errors should be logged via loggingManager.py
- Critical errors should be reported to the bot owner

