"""
Management Commands

Commands for managing scheduled messages (list, edit, cancel).
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from dateutil import parser
import pytz
import logging

logger = logging.getLogger(__name__)


class ManagementCommands(commands.Cog):
    """
    Commands for managing scheduled messages.
    
    Includes /list_scheduled, /cancel_scheduled, and /edit_scheduled commands.
    """
    
    def __init__(self, bot):
        """Initialize the cog with the bot instance."""
        self.bot = bot
    
    @app_commands.command(
        name="list_scheduled",
        description="List your scheduled messages"
    )
    @app_commands.describe(
        status="Filter by status (optional): pending, sent, failed, cancelled"
    )
    async def list_scheduled(
        self,
        interaction: discord.Interaction,
        status: str = None
    ):
        """
        List all scheduled messages for the user.
        
        Users can optionally filter by status.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate status if provided
            valid_statuses = ['pending', 'sent', 'failed', 'cancelled']
            if status and status.lower() not in valid_statuses:
                await interaction.followup.send(
                    f"❌ Invalid status! Valid options are: {', '.join(valid_statuses)}",
                    ephemeral=True
                )
                return
            
            # Get user's scheduled messages
            messages = await self.bot.appwrite_client.list_scheduled_messages_for_user(
                str(interaction.user.id),
                status=status.lower() if status else None
            )
            
            if not messages:
                status_text = f" with status '{status}'" if status else ""
                await interaction.followup.send(
                    f"📭 You don't have any scheduled messages{status_text}.",
                    ephemeral=True
                )
                return
            
            # Create embeds for messages (max 10 fields per embed)
            embeds = []
            current_embed = discord.Embed(
                title="📅 Your Scheduled Messages",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            if status:
                current_embed.description = f"Showing messages with status: **{status}**"
            
            field_count = 0
            
            for msg in messages[:25]:  # Limit to 25 messages
                # Parse datetime
                scheduled_time = datetime.fromisoformat(msg['scheduled_time'].replace('Z', '+00:00'))
                time_str = scheduled_time.strftime("%Y-%m-%d %H:%M UTC")
                
                # Format target
                target_type = msg['target_type']
                target_id = msg['target_id']
                
                if target_type == "dm":
                    target_str = f"DM to <@{target_id}>"
                elif target_type == "thread":
                    target_str = f"Thread <#{target_id}>"
                else:
                    target_str = f"Channel <#{target_id}>"
                
                # Status emoji
                status_emoji = {
                    'pending': '⏳',
                    'sent': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }.get(msg['status'], '❓')
                
                # Create field
                field_name = f"{status_emoji} {msg['status'].title()} - ID: `{msg['$id'][:8]}...`"
                field_value = (
                    f"**Target:** {target_str}\n"
                    f"**Time:** {time_str}\n"
                    f"**Message:** {msg['message_content'][:50]}{'...' if len(msg['message_content']) > 50 else ''}"
                )
                
                current_embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False
                )
                
                field_count += 1
                
                # Discord has a limit of 25 fields per embed
                if field_count >= 10:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title="📅 Your Scheduled Messages (continued)",
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    )
                    field_count = 0
            
            # Add the last embed if it has fields
            if field_count > 0:
                embeds.append(current_embed)
            
            # Add footer to last embed
            if embeds:
                embeds[-1].set_footer(text=f"Total: {len(messages)} messages")
            
            # Send embeds
            for embed in embeds:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing scheduled messages: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while listing your messages: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="cancel_scheduled",
        description="Cancel a scheduled message"
    )
    @app_commands.describe(
        message_id="The ID of the scheduled message to cancel"
    )
    async def cancel_scheduled(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):
        """
        Cancel a scheduled message.
        
        Only the user who scheduled the message can cancel it.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get the scheduled message
            message = await self.bot.appwrite_client.get_scheduled_message(message_id)
            
            if not message:
                await interaction.followup.send(
                    f"❌ Scheduled message with ID `{message_id}` not found.",
                    ephemeral=True
                )
                return
            
            # Verify ownership
            if message['discord_user_id'] != str(interaction.user.id):
                await interaction.followup.send(
                    "❌ You can only cancel your own scheduled messages!",
                    ephemeral=True
                )
                return
            
            # Check if already cancelled or sent
            if message['status'] in ['cancelled', 'sent', 'failed']:
                await interaction.followup.send(
                    f"❌ This message has already been {message['status']}!",
                    ephemeral=True
                )
                return
            
            # Cancel the message
            await self.bot.appwrite_client.cancel_scheduled_message(message_id)
            
            # Create response embed
            embed = discord.Embed(
                title="🚫 Message Cancelled",
                description="Your scheduled message has been cancelled.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="Message ID",
                value=f"`{message_id}`",
                inline=False
            )
            embed.add_field(
                name="Message Preview",
                value=message['message_content'][:100] + ("..." if len(message['message_content']) > 100 else ""),
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"User {interaction.user.id} cancelled message {message_id}")
            
        except Exception as e:
            logger.error(f"Error cancelling scheduled message: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while cancelling your message: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="edit_scheduled",
        description="Edit a scheduled message's time or content"
    )
    @app_commands.describe(
        message_id="The ID of the scheduled message to edit",
        new_time="New time to send the message (optional)",
        new_message="New message content (optional)"
    )
    async def edit_scheduled(
        self,
        interaction: discord.Interaction,
        message_id: str,
        new_time: str = None,
        new_message: str = None
    ):
        """
        Edit a scheduled message's time or content.
        
        At least one of new_time or new_message must be provided.
        Only pending messages can be edited.
        """
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check that at least one parameter is provided
            if not new_time and not new_message:
                await interaction.followup.send(
                    "❌ You must provide at least one of `new_time` or `new_message` to edit!",
                    ephemeral=True
                )
                return
            
            # Get the scheduled message
            message = await self.bot.appwrite_client.get_scheduled_message(message_id)
            
            if not message:
                await interaction.followup.send(
                    f"❌ Scheduled message with ID `{message_id}` not found.",
                    ephemeral=True
                )
                return
            
            # Verify ownership
            if message['discord_user_id'] != str(interaction.user.id):
                await interaction.followup.send(
                    "❌ You can only edit your own scheduled messages!",
                    ephemeral=True
                )
                return
            
            # Check if message is pending
            if message['status'] != 'pending':
                await interaction.followup.send(
                    f"❌ You can only edit pending messages! This message is {message['status']}.",
                    ephemeral=True
                )
                return
            
            # Prepare updates
            updates = {}
            
            # Parse new time if provided
            if new_time:
                try:
                    # Get user preferences for timezone
                    prefs = await self.bot.appwrite_client.get_user_preferences(str(interaction.user.id))
                    user_tz = prefs.get('timezone', 'UTC')
                    
                    # Parse time (reuse parse_time from schedule_commands)
                    from commands.schedule_commands import ScheduleCommands
                    schedule_cog = ScheduleCommands(self.bot)
                    scheduled_time = schedule_cog.parse_time(new_time, user_tz)
                    
                    # Validate that the new time is in the future
                    if scheduled_time <= datetime.utcnow():
                        await interaction.followup.send(
                            "❌ The new scheduled time must be in the future!",
                            ephemeral=True
                        )
                        return
                    
                    updates['scheduled_time'] = scheduled_time.isoformat()
                    
                except ValueError as e:
                    await interaction.followup.send(
                        f"❌ Invalid time format: {str(e)}",
                        ephemeral=True
                    )
                    return
            
            # Update message content if provided
            if new_message:
                updates['message_content'] = new_message
            
            # Apply updates
            updated_message = await self.bot.appwrite_client.update_scheduled_message(
                message_id,
                **updates
            )
            
            # Create response embed
            embed = discord.Embed(
                title="✏️ Message Updated",
                description="Your scheduled message has been updated.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="Message ID",
                value=f"`{message_id}`",
                inline=False
            )
            
            if new_time:
                time_str = datetime.fromisoformat(updated_message['scheduled_time'].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M UTC")
                embed.add_field(
                    name="New Time",
                    value=time_str,
                    inline=True
                )
            
            if new_message:
                embed.add_field(
                    name="New Message Preview",
                    value=new_message[:100] + ("..." if len(new_message) > 100 else ""),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"User {interaction.user.id} edited message {message_id}")
            
        except Exception as e:
            logger.error(f"Error editing scheduled message: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred while editing your message: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Required setup function for loading the cog."""
    await bot.add_cog(ManagementCommands(bot))

