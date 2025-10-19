"""
Utility Commands

Helper commands for the bot (help, preferences, timezone, etc.).
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)


class UtilityCommands(commands.Cog):
    """
    Utility commands for the bot.
    
    Includes /help, /set_timezone, /preferences commands.
    """
    
    def __init__(self, bot):
        """Initialize the cog with the bot instance."""
        self.bot = bot
    
    @app_commands.command(
        name="help",
        description="Show help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        """
        Display help information about available commands.
        """
        embed = discord.Embed(
            title="📋 Discord Message Scheduler - Help",
            description="Schedule messages to be sent at a specific time to channels, threads, or DMs.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Scheduling Commands
        embed.add_field(
            name="📅 Scheduling Commands",
            value=(
                "`/schedule_message` - Schedule a message to a channel or thread\n"
                "`/schedule_dm` - Schedule a direct message to a user\n"
            ),
            inline=False
        )
        
        # Management Commands
        embed.add_field(
            name="🔧 Management Commands",
            value=(
                "`/list_scheduled` - View all your scheduled messages\n"
                "`/edit_scheduled` - Edit a scheduled message's time or content\n"
                "`/cancel_scheduled` - Cancel a scheduled message\n"
            ),
            inline=False
        )
        
        # Utility Commands
        embed.add_field(
            name="⚙️ Utility Commands",
            value=(
                "`/set_timezone` - Set your timezone for scheduling\n"
                "`/preferences` - View and update your preferences\n"
                "`/help` - Show this help message\n"
            ),
            inline=False
        )
        
        # Time Format Examples
        embed.add_field(
            name="⏰ Time Format Examples",
            value=(
                "• `2024-12-25 14:30` - Specific date and time\n"
                "• `tomorrow at 3pm` - Natural language\n"
                "• `in 2 hours` - Relative time\n"
                "• `next friday at 10am` - Day of week\n"
            ),
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 Tips",
            value=(
                "• All messages are scheduled in UTC unless you set a timezone\n"
                "• Use `/set_timezone` to schedule in your local time\n"
                "• You can schedule up to 10 pending messages by default\n"
                "• Only pending messages can be edited or cancelled\n"
            ),
            inline=False
        )
        
        embed.set_footer(text="Made with ❤️ using Appwrite")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="set_timezone",
        description="Set your timezone for scheduling messages"
    )
    @app_commands.describe(
        timezone="Your timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')"
    )
    async def set_timezone(
        self,
        interaction: discord.Interaction,
        timezone: str
    ):
        """
        Set the user's timezone preference.
        
        This affects how scheduled times are interpreted.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate timezone
            try:
                pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                await interaction.followup.send(
                    f"❌ Unknown timezone: `{timezone}`\n\n"
                    f"Please use a valid IANA timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo').\n"
                    f"You can find a list at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                    ephemeral=True
                )
                return
            
            # Update user preferences
            await self.bot.appwrite_client.update_user_preferences(
                str(interaction.user.id),
                timezone=timezone
            )
            
            # Get current time in the new timezone
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            
            embed = discord.Embed(
                title="🌍 Timezone Updated",
                description=f"Your timezone has been set to **{timezone}**",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="Current Time in Your Timezone",
                value=current_time,
                inline=False
            )
            embed.add_field(
                name="Note",
                value="Future scheduled messages will use this timezone for time parsing.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"User {interaction.user.id} set timezone to {timezone}")
            
        except Exception as e:
            logger.error(f"Error setting timezone: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while setting your timezone: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="preferences",
        description="View and update your preferences"
    )
    @app_commands.describe(
        notifications="Enable/disable notifications (optional): true or false"
    )
    async def preferences(
        self,
        interaction: discord.Interaction,
        notifications: bool = None
    ):
        """
        View and update user preferences.
        
        Users can enable/disable notifications for scheduled message status updates.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Update notifications if provided
            if notifications is not None:
                await self.bot.appwrite_client.update_user_preferences(
                    str(interaction.user.id),
                    notification_enabled=notifications
                )
            
            # Get current preferences
            prefs = await self.bot.appwrite_client.get_user_preferences(str(interaction.user.id))
            
            # Create embed
            embed = discord.Embed(
                title="⚙️ Your Preferences",
                description="Current settings for your account",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🌍 Timezone",
                value=prefs.get('timezone', 'UTC'),
                inline=True
            )
            
            embed.add_field(
                name="📬 Notifications",
                value="✅ Enabled" if prefs.get('notification_enabled', True) else "❌ Disabled",
                inline=True
            )
            
            embed.add_field(
                name="📊 Max Scheduled Messages",
                value=str(prefs.get('max_scheduled_messages', 10)),
                inline=True
            )
            
            # Count pending messages
            pending_messages = await self.bot.appwrite_client.list_scheduled_messages_for_user(
                str(interaction.user.id),
                status="pending"
            )
            
            embed.add_field(
                name="📝 Current Pending Messages",
                value=f"{len(pending_messages)} / {prefs.get('max_scheduled_messages', 10)}",
                inline=True
            )
            
            embed.set_footer(text="Use /set_timezone to change your timezone")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            if notifications is not None:
                status = "enabled" if notifications else "disabled"
                logger.info(f"User {interaction.user.id} {status} notifications")
            
        except Exception as e:
            logger.error(f"Error managing preferences: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while managing your preferences: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Required setup function for loading the cog."""
    await bot.add_cog(UtilityCommands(bot))

