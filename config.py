"""
Configuration module for Discord Message Scheduler Bot

Loads environment variables and provides configuration constants.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # Optional: for development/testing

# Appwrite Configuration
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "discord_scheduler_db")

# Collection IDs (must match setup_appwrite.py)
COLLECTION_SCHEDULED_MESSAGES = "scheduled_messages"
COLLECTION_USER_PREFERENCES = "user_preferences"
COLLECTION_EXECUTION_LOGS = "execution_logs"

# Bot Configuration
SCHEDULER_CHECK_INTERVAL = int(os.getenv("SCHEDULER_CHECK_INTERVAL", "60"))
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validation
def validate_config():
    """Validate that all required configuration is present."""
    required_vars = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "APPWRITE_ENDPOINT": APPWRITE_ENDPOINT,
        "APPWRITE_PROJECT_ID": APPWRITE_PROJECT_ID,
        "APPWRITE_API_KEY": APPWRITE_API_KEY,
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file or environment configuration."
        )
    
    return True

