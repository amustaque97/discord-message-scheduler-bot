"""
Discord Message Scheduler Bot

A Discord bot that allows users to schedule messages to channels, threads, and DMs
using Appwrite as the backend database.

Usage:
    python bot.py
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from datetime import datetime

import config
from scheduler_service import SchedulerService
from appwrite_client import AppwriteClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SchedulerBot(commands.Bot):
    """
    Discord bot for scheduling messages.
    
    Features:
    - Schedule messages to channels, threads, and DMs
    - List, edit, and cancel scheduled messages
    - Background task to process scheduled messages
    """
    
    def __init__(self):
        """Initialize the bot with required intents and configuration."""
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content access
        intents.guilds = True
        intents.members = True  # Optional: for better user handling
        
        super().__init__(
            command_prefix='!',  # Fallback prefix (we'll use slash commands)
            intents=intents,
            help_command=None  # We'll create a custom help command
        )
        
        # Initialize services
        self.appwrite_client = None
        self.scheduler_service = None
        
    async def setup_hook(self):
        """
        Async initialization that runs before the bot starts.
        
        This is where we:
        - Initialize the Appwrite client
        - Set up the scheduler service
        - Register slash commands
        """
        logger.info("Setting up bot...")
        
        # Initialize Appwrite client
        self.appwrite_client = AppwriteClient()
        logger.info("Appwrite client initialized")
        
        # Initialize scheduler service
        self.scheduler_service = SchedulerService(self, self.appwrite_client)
        logger.info("Scheduler service initialized")
        
        # Sync commands to Discord
        if config.DISCORD_GUILD_ID:
            # For development: sync to specific guild (instant)
            guild = discord.Object(id=int(config.DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Commands synced to guild {config.DISCORD_GUILD_ID}")
        else:
            # For production: sync globally (can take up to 1 hour)
            await self.tree.sync()
            logger.info("Commands synced globally")
    
    async def on_ready(self):
        """
        Event handler called when the bot is ready and connected to Discord.
        """
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /schedule_message"
            )
        )
        
        # Start the scheduler service
        self.loop.create_task(self.scheduler_service.start())
        logger.info("Scheduler service started")
    
    async def on_command_error(self, ctx, error):
        """
        Global error handler for commands.
        """
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        logger.error(f"Command error: {error}", exc_info=error)
        
        if ctx.interaction:
            await ctx.interaction.response.send_message(
                f"❌ An error occurred: {str(error)}",
                ephemeral=True
            )
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Global error handler for slash commands.
        """
        logger.error(f"App command error: {error}", exc_info=error)
        
        error_message = "❌ An error occurred while executing the command."
        
        if isinstance(error, app_commands.MissingPermissions):
            error_message = "❌ You don't have permission to use this command."
        elif isinstance(error, app_commands.CommandOnCooldown):
            error_message = f"❌ This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, app_commands.BotMissingPermissions):
            error_message = "❌ I don't have the required permissions to execute this command."
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")


async def main():
    """
    Main entry point for the bot.
    
    Validates configuration, initializes the bot, and starts it.
    """
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        config.validate_config()
        logger.info("Configuration validated successfully")
        
        # Initialize bot
        bot = SchedulerBot()
        
        # Load command cogs
        from commands import schedule_commands, management_commands, utils_commands
        
        await bot.add_cog(schedule_commands.ScheduleCommands(bot))
        logger.info("Schedule commands loaded")
        
        await bot.add_cog(management_commands.ManagementCommands(bot))
        logger.info("Management commands loaded")
        
        await bot.add_cog(utils_commands.UtilityCommands(bot))
        logger.info("Utility commands loaded")
        
        # Start the bot
        logger.info("Starting bot...")
        await bot.start(config.DISCORD_TOKEN)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

