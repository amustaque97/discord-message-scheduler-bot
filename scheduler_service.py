"""
Scheduler Service

Background service that periodically checks for due scheduled messages
and sends them via the Discord bot.
"""

import discord
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging

import config

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background service for processing scheduled messages.
    
    Periodically checks the Appwrite database for pending messages
    that are due to be sent, sends them, and logs the results.
    """
    
    def __init__(self, bot, appwrite_client):
        """
        Initialize the scheduler service.
        
        Args:
            bot: The Discord bot instance
            appwrite_client: The Appwrite client for database operations
        """
        self.bot = bot
        self.appwrite_client = appwrite_client
        self.running = False
        self.check_interval = config.SCHEDULER_CHECK_INTERVAL
    
    async def start(self):
        """
        Start the scheduler service.
        
        This method runs indefinitely, checking for scheduled messages
        at regular intervals defined by SCHEDULER_CHECK_INTERVAL.
        """
        if self.running:
            logger.warning("Scheduler service is already running")
            return
        
        self.running = True
        logger.info(f"Scheduler service started (checking every {self.check_interval} seconds)")
        
        while self.running:
            try:
                await self.process_scheduled_messages()
            except Exception as e:
                logger.error(f"Error in scheduler service: {e}", exc_info=True)
            
            # Wait for the next check interval
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the scheduler service."""
        self.running = False
        logger.info("Scheduler service stopped")
    
    async def process_scheduled_messages(self):
        """
        Check for and process all pending scheduled messages that are due.
        
        This method:
        1. Queries the database for pending messages
        2. Attempts to send each message
        3. Updates the database with results
        4. Creates execution logs
        """
        try:
            # Get current time
            current_time = datetime.utcnow()
            
            # Query for pending messages that are due
            pending_messages = await self.appwrite_client.get_pending_messages(current_time)
            
            if not pending_messages:
                # No messages to process
                return
            
            logger.info(f"Processing {len(pending_messages)} pending messages")
            
            # Process each message
            for message_doc in pending_messages:
                try:
                    await self.send_scheduled_message(message_doc)
                except Exception as e:
                    logger.error(
                        f"Failed to process message {message_doc['$id']}: {e}",
                        exc_info=True
                    )
            
        except Exception as e:
            logger.error(f"Error processing scheduled messages: {e}", exc_info=True)
    
    async def send_scheduled_message(self, message_doc: Dict[str, Any]):
        """
        Send a single scheduled message.
        
        Args:
            message_doc: The scheduled message document from Appwrite
        """
        message_id = message_doc['$id']
        target_type = message_doc['target_type']
        target_id = message_doc['target_id']
        content = message_doc['message_content']
        discord_user_id = message_doc['discord_user_id']
        retry_count = message_doc.get('retry_count', 0)
        
        logger.info(f"Attempting to send message {message_id} to {target_type} {target_id}")
        
        try:
            # Send the message based on target type
            if target_type == "channel":
                await self.send_to_channel(target_id, content)
            elif target_type == "thread":
                await self.send_to_thread(target_id, content)
            elif target_type == "dm":
                await self.send_to_dm(target_id, content, discord_user_id)
            else:
                raise ValueError(f"Unknown target type: {target_type}")
            
            # Mark as sent
            await self.appwrite_client.mark_message_as_sent(message_id)
            
            # Create success log
            await self.appwrite_client.create_execution_log(
                scheduled_message_id=message_id,
                discord_user_id=discord_user_id,
                target_type=target_type,
                target_id=target_id,
                status="success",
                message_preview=content[:200]
            )
            
            logger.info(f"Successfully sent message {message_id}")
            
            # Optionally notify the user
            await self.notify_user(discord_user_id, message_id, "sent", content)
            
        except discord.Forbidden as e:
            # Permission error - mark as failed
            error_msg = f"Permission denied: {str(e)}"
            logger.error(f"Permission error for message {message_id}: {error_msg}")
            
            await self.appwrite_client.mark_message_as_failed(
                message_id,
                error_msg,
                config.MAX_RETRY_ATTEMPTS  # Don't retry permission errors
            )
            
            await self.appwrite_client.create_execution_log(
                scheduled_message_id=message_id,
                discord_user_id=discord_user_id,
                target_type=target_type,
                target_id=target_id,
                status="failed",
                error_message=error_msg,
                message_preview=content[:200]
            )
            
            await self.notify_user(discord_user_id, message_id, "failed", content, error_msg)
            
        except discord.NotFound as e:
            # Target not found - mark as failed
            error_msg = f"Target not found: {str(e)}"
            logger.error(f"Target not found for message {message_id}: {error_msg}")
            
            await self.appwrite_client.mark_message_as_failed(
                message_id,
                error_msg,
                config.MAX_RETRY_ATTEMPTS  # Don't retry not found errors
            )
            
            await self.appwrite_client.create_execution_log(
                scheduled_message_id=message_id,
                discord_user_id=discord_user_id,
                target_type=target_type,
                target_id=target_id,
                status="failed",
                error_message=error_msg,
                message_preview=content[:200]
            )
            
            await self.notify_user(discord_user_id, message_id, "failed", content, error_msg)
            
        except Exception as e:
            # Other errors - retry if within limit
            error_msg = f"Error: {str(e)}"
            logger.error(f"Error sending message {message_id}: {error_msg}")
            
            new_retry_count = retry_count + 1
            
            await self.appwrite_client.mark_message_as_failed(
                message_id,
                error_msg,
                new_retry_count
            )
            
            status = "retrying" if new_retry_count < config.MAX_RETRY_ATTEMPTS else "failed"
            
            await self.appwrite_client.create_execution_log(
                scheduled_message_id=message_id,
                discord_user_id=discord_user_id,
                target_type=target_type,
                target_id=target_id,
                status=status,
                error_message=error_msg,
                message_preview=content[:200]
            )
            
            if status == "failed":
                await self.notify_user(discord_user_id, message_id, "failed", content, error_msg)
    
    async def send_to_channel(self, channel_id: str, content: str):
        """
        Send a message to a channel.
        
        Args:
            channel_id: Discord channel ID
            content: Message content
            
        Raises:
            discord.NotFound: If channel doesn't exist
            discord.Forbidden: If bot lacks permission
        """
        channel = self.bot.get_channel(int(channel_id))
        
        if channel is None:
            # Try fetching if not in cache
            channel = await self.bot.fetch_channel(int(channel_id))
        
        await channel.send(content)
    
    async def send_to_thread(self, thread_id: str, content: str):
        """
        Send a message to a thread.
        
        Args:
            thread_id: Discord thread ID
            content: Message content
            
        Raises:
            discord.NotFound: If thread doesn't exist
            discord.Forbidden: If bot lacks permission
        """
        # Threads are accessed the same way as channels
        thread = self.bot.get_channel(int(thread_id))
        
        if thread is None:
            thread = await self.bot.fetch_channel(int(thread_id))
        
        await thread.send(content)
    
    async def send_to_dm(self, user_id: str, content: str, scheduler_user_id: str):
        """
        Send a direct message to a user.
        
        Args:
            user_id: Discord user ID to send DM to
            content: Message content
            scheduler_user_id: User ID who scheduled the message
            
        Raises:
            discord.Forbidden: If user has DMs disabled
            discord.NotFound: If user doesn't exist
        """
        user = self.bot.get_user(int(user_id))
        
        if user is None:
            user = await self.bot.fetch_user(int(user_id))
        
        # Add a note about who scheduled the message
        scheduler = self.bot.get_user(int(scheduler_user_id))
        scheduler_name = scheduler.name if scheduler else "someone"
        
        full_content = f"📨 *Scheduled message from {scheduler_name}:*\n\n{content}"
        
        await user.send(full_content)
    
    async def notify_user(
        self,
        user_id: str,
        message_id: str,
        status: str,
        content: str,
        error: str = None
    ):
        """
        Notify the user about the status of their scheduled message.
        
        Args:
            user_id: Discord user ID
            message_id: Scheduled message ID
            status: Status ('sent' or 'failed')
            content: Message content
            error: Optional error message
        """
        try:
            # Get user preferences
            prefs = await self.appwrite_client.get_user_preferences(user_id)
            
            # Check if notifications are enabled
            if not prefs.get('notification_enabled', True):
                return
            
            # Get user
            user = self.bot.get_user(int(user_id))
            if user is None:
                user = await self.bot.fetch_user(int(user_id))
            
            # Create notification embed
            if status == "sent":
                embed = discord.Embed(
                    title="✅ Scheduled Message Sent",
                    description="Your scheduled message was sent successfully!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
            else:  # failed
                embed = discord.Embed(
                    title="❌ Scheduled Message Failed",
                    description="Your scheduled message could not be sent.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                if error:
                    embed.add_field(name="Error", value=error, inline=False)
            
            embed.add_field(
                name="Message ID",
                value=f"`{message_id}`",
                inline=False
            )
            embed.add_field(
                name="Content Preview",
                value=content[:100] + ("..." if len(content) > 100 else ""),
                inline=False
            )
            
            await user.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            # Don't raise - notification failures shouldn't stop the service

