"""
Configuration settings for SennaBot.
"""
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Bot identification
OWNER_ID = int(os.getenv("OWNER_ID", 163705957983977473))
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Target users for special features
TARGET_USER_ID_STR = os.getenv("TARGET_USER_ID", "")
TARGET_USER_ID = [int(id.strip()) for id in TARGET_USER_ID_STR.split(",")] if TARGET_USER_ID_STR else []

# Bot configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() in ["true", "1", "yes"]
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Framework settings
DATA_PATH = os.getenv("DATA_PATH", "data")
LOGS_PATH = os.getenv("LOGS_PATH", "logs")
OWNER_GUILD_ID = os.getenv("OWNER_GUILD_ID", "1349273253343920210")

# Economy settings (will move to data/config/bot_settings.json)
STARTING_BALANCE = int(os.getenv("STARTING_BALANCE", 50))
CRITICAL_SUCCESS_CHANCE = int(os.getenv("CRITICAL_SUCCESS_CHANCE", 2))
CRITICAL_MULTIPLIER_MIN = int(os.getenv("CRITICAL_MULTIPLIER_MIN", 3))
CRITICAL_MULTIPLIER_MAX = int(os.getenv("CRITICAL_MULTIPLIER_MAX", 5))