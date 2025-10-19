"""
Schedule Commands

Slash commands for scheduling messages to channels, threads, and DMs.
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import logging

logger = logging.getLogger(__name__)


class ScheduleCommands(commands.Cog):
    """
    Commands for scheduling messages.
    
    Includes /schedule_message and /schedule_dm commands.
    """
    
    def __init__(self, bot):
        """Initialize the cog with the bot instance."""
        self.bot = bot
    
    def parse_time(self, time_str: str, user_timezone: str = "UTC") -> datetime:
        """
        Parse a time string into a datetime object.
        
        Supports formats like:
        - "2024-12-25 14:30"
        - "tomorrow at 3pm"
        - "in 2 hours"
        - "next friday at 10am"
        
        Args:
            time_str: Time string to parse
            user_timezone: User's timezone (default: UTC)
            
        Returns:
            Parsed datetime in UTC
            
        Raises:
            ValueError: If time string cannot be parsed
        """
        try:
            # Try to parse relative times (in X hours, in X minutes)
            if time_str.lower().startswith("in "):
                parts = time_str.lower().replace("in ", "").strip().split()
                amount = int(parts[0])
                unit = parts[1] if len(parts) > 1 else "minutes"
                
                if "hour" in unit:
                    return datetime.utcnow() + timedelta(hours=amount)
                elif "minute" in unit or "min" in unit:
                    return datetime.utcnow() + timedelta(minutes=amount)
                elif "day" in unit:
                    return datetime.utcnow() + timedelta(days=amount)
                else:
                    raise ValueError(f"Unknown time unit: {unit}")
            
            # Try to parse absolute times
            tz = pytz.timezone(user_timezone)
            parsed = parser.parse(time_str, fuzzy=True)
            
            # If no timezone info, assume user's timezone
            if parsed.tzinfo is None:
                parsed = tz.localize(parsed)
            
            # Convert to UTC
            return parsed.astimezone(pytz.UTC).replace(tzinfo=None)
            
        except Exception as e:
            raise ValueError(f"Could not parse time '{time_str}': {str(e)}")
    
    @app_commands.command(
        name="schedule_message",
        description="Schedule a message to be sent to a channel or thread"
    )
    @app_commands.describe(
        channel="The channel where the message will be sent",
        message="The message content to send",
        time="When to send (e.g., '2024-12-25 14:30', 'tomorrow at 3pm', 'in 2 hours')",
        thread="Optional: The thread where the message will be sent"
    )
    async def schedule_message(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
        time: str,
        thread: discord.Thread = None
    ):
        """
        Schedule a message to be sent to a channel or thread.
        
        This command allows users to schedule messages to channels they have access to.
        The bot must have permission to send messages in the target channel.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get user preferences for timezone
            prefs = await self.bot.appwrite_client.get_user_preferences(str(interaction.user.id))
            user_tz = prefs.get('timezone', 'UTC')
            
            # Parse the scheduled time
            try:
                scheduled_time = self.parse_time(time, user_tz)
            except ValueError as e:
                await interaction.followup.send(
                    f"❌ Invalid time format: {str(e)}\n\n"
                    f"Examples of valid formats:\n"
                    f"• `2024-12-25 14:30`\n"
                    f"• `tomorrow at 3pm`\n"
                    f"• `in 2 hours`\n"
                    f"• `next friday at 10am`",
                    ephemeral=True
                )
                return
            
            # Validate that the scheduled time is in the future
            if scheduled_time <= datetime.utcnow():
                await interaction.followup.send(
                    "❌ The scheduled time must be in the future!",
                    ephemeral=True
                )
                return
            
            # Check permissions
            target = thread if thread else channel
            if not target.permissions_for(interaction.guild.me).send_messages:
                await interaction.followup.send(
                    f"❌ I don't have permission to send messages in {target.mention}!",
                    ephemeral=True
                )
                return
            
            # Check user's scheduled message limit
            pending_messages = await self.bot.appwrite_client.list_scheduled_messages_for_user(
                str(interaction.user.id),
                status="pending"
            )
            max_messages = prefs.get('max_scheduled_messages', 10)
            
            if len(pending_messages) >= max_messages:
                await interaction.followup.send(
                    f"❌ You've reached your limit of {max_messages} pending scheduled messages!\n"
                    f"Cancel or wait for some messages to be sent before scheduling more.",
                    ephemeral=True
                )
                return
            
            # Determine target type and IDs
            if thread:
                target_type = "thread"
                target_id = str(thread.id)
                thread_id = str(thread.id)
            else:
                target_type = "channel"
                target_id = str(channel.id)
                thread_id = None
            
            # Create scheduled message in database
            doc = await self.bot.appwrite_client.create_scheduled_message(
                discord_user_id=str(interaction.user.id),
                target_type=target_type,
                target_id=target_id,
                message_content=message,
                scheduled_time=scheduled_time,
                guild_id=str(interaction.guild.id),
                thread_id=thread_id
            )
            
            # Format time for display
            display_time = scheduled_time.strftime("%Y-%m-%d %H:%M UTC")
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Message Scheduled",
                description=f"Your message has been scheduled successfully!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="📍 Target",
                value=target.mention,
                inline=True
            )
            embed.add_field(
                name="⏰ Scheduled Time",
                value=display_time,
                inline=True
            )
            embed.add_field(
                name="🆔 Message ID",
                value=f"`{doc['$id']}`",
                inline=False
            )
            embed.add_field(
                name="📝 Message Preview",
                value=message[:100] + ("..." if len(message) > 100 else ""),
                inline=False
            )
            embed.set_footer(text=f"Use /list_scheduled to view all your scheduled messages")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(
                f"User {interaction.user.id} scheduled message {doc['$id']} "
                f"for {display_time} in {target_type} {target_id}"
            )
            
        except Exception as e:
            logger.error(f"Error scheduling message: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while scheduling your message: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="schedule_dm",
        description="Schedule a direct message to be sent to a user"
    )
    @app_commands.describe(
        user="The user who will receive the message",
        message="The message content to send",
        time="When to send (e.g., '2024-12-25 14:30', 'tomorrow at 3pm', 'in 2 hours')"
    )
    async def schedule_dm(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        message: str,
        time: str
    ):
        """
        Schedule a direct message to be sent to a user.
        
        The bot will send the DM on your behalf at the scheduled time.
        Note: The recipient will see the message coming from the bot, not from you.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is trying to DM themselves
            if user.id == interaction.user.id:
                await interaction.followup.send(
                    "❌ You cannot schedule a message to yourself!",
                    ephemeral=True
                )
                return
            
            # Check if user is trying to DM a bot
            if user.bot:
                await interaction.followup.send(
                    "❌ You cannot schedule messages to bots!",
                    ephemeral=True
                )
                return
            
            # Get user preferences for timezone
            prefs = await self.bot.appwrite_client.get_user_preferences(str(interaction.user.id))
            user_tz = prefs.get('timezone', 'UTC')
            
            # Parse the scheduled time
            try:
                scheduled_time = self.parse_time(time, user_tz)
            except ValueError as e:
                await interaction.followup.send(
                    f"❌ Invalid time format: {str(e)}\n\n"
                    f"Examples of valid formats:\n"
                    f"• `2024-12-25 14:30`\n"
                    f"• `tomorrow at 3pm`\n"
                    f"• `in 2 hours`\n"
                    f"• `next friday at 10am`",
                    ephemeral=True
                )
                return
            
            # Validate that the scheduled time is in the future
            if scheduled_time <= datetime.utcnow():
                await interaction.followup.send(
                    "❌ The scheduled time must be in the future!",
                    ephemeral=True
                )
                return
            
            # Check user's scheduled message limit
            pending_messages = await self.bot.appwrite_client.list_scheduled_messages_for_user(
                str(interaction.user.id),
                status="pending"
            )
            max_messages = prefs.get('max_scheduled_messages', 10)
            
            if len(pending_messages) >= max_messages:
                await interaction.followup.send(
                    f"❌ You've reached your limit of {max_messages} pending scheduled messages!\n"
                    f"Cancel or wait for some messages to be sent before scheduling more.",
                    ephemeral=True
                )
                return
            
            # Create scheduled message in database
            doc = await self.bot.appwrite_client.create_scheduled_message(
                discord_user_id=str(interaction.user.id),
                target_type="dm",
                target_id=str(user.id),
                message_content=message,
                scheduled_time=scheduled_time,
                guild_id=str(interaction.guild.id) if interaction.guild else None
            )
            
            # Format time for display
            display_time = scheduled_time.strftime("%Y-%m-%d %H:%M UTC")
            
            # Create success embed
            embed = discord.Embed(
                title="✅ DM Scheduled",
                description=f"Your direct message has been scheduled successfully!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="👤 Recipient",
                value=user.mention,
                inline=True
            )
            embed.add_field(
                name="⏰ Scheduled Time",
                value=display_time,
                inline=True
            )
            embed.add_field(
                name="🆔 Message ID",
                value=f"`{doc['$id']}`",
                inline=False
            )
            embed.add_field(
                name="📝 Message Preview",
                value=message[:100] + ("..." if len(message) > 100 else ""),
                inline=False
            )
            embed.set_footer(text=f"Use /list_scheduled to view all your scheduled messages")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(
                f"User {interaction.user.id} scheduled DM {doc['$id']} "
                f"for {display_time} to user {user.id}"
            )
            
        except Exception as e:
            logger.error(f"Error scheduling DM: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while scheduling your DM: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Required setup function for loading the cog."""
    await bot.add_cog(ScheduleCommands(bot))

