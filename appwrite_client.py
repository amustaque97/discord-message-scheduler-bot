"""
Appwrite Client

Provides a wrapper around the Appwrite SDK with helper functions
for database operations related to the Discord Message Scheduler.
"""

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
from appwrite.exception import AppwriteException
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

import config

logger = logging.getLogger(__name__)


class AppwriteClient:
    """
    Wrapper for Appwrite database operations.
    
    Provides helper methods for CRUD operations on scheduled messages,
    user preferences, and execution logs.
    """
    
    def __init__(self):
        """Initialize the Appwrite client with configuration from environment."""
        self.client = Client()
        self.client.set_endpoint(config.APPWRITE_ENDPOINT)
        self.client.set_project(config.APPWRITE_PROJECT_ID)
        self.client.set_key(config.APPWRITE_API_KEY)
        
        self.databases = Databases(self.client)
        self.database_id = config.APPWRITE_DATABASE_ID
        
        logger.info("Appwrite client initialized")
    
    # ==================== Scheduled Messages ====================
    
    async def create_scheduled_message(
        self,
        discord_user_id: str,
        target_type: str,
        target_id: str,
        message_content: str,
        scheduled_time: datetime,
        guild_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new scheduled message in the database.
        
        Args:
            discord_user_id: Discord user ID who scheduled the message
            target_type: Type of target ('channel', 'dm', or 'thread')
            target_id: Discord ID of the target
            message_content: Content of the message to be sent
            scheduled_time: When the message should be sent (datetime object)
            guild_id: Optional Discord server/guild ID
            thread_id: Optional thread ID
            
        Returns:
            The created document as a dictionary
            
        Raises:
            AppwriteException: If the creation fails
        """
        try:
            document = {
                "discord_user_id": discord_user_id,
                "target_type": target_type,
                "target_id": target_id,
                "message_content": message_content,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "retry_count": 0
            }
            
            # Add optional fields if provided
            if guild_id:
                document["guild_id"] = guild_id
            if thread_id:
                document["thread_id"] = thread_id
            
            result = self.databases.create_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                document_id='unique()',
                data=document
            )
            
            logger.info(f"Created scheduled message {result['$id']} for user {discord_user_id}")
            return result
            
        except AppwriteException as e:
            logger.error(f"Failed to create scheduled message: {e}")
            raise
    
    async def get_scheduled_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a scheduled message by its ID.
        
        Args:
            message_id: The Appwrite document ID
            
        Returns:
            The document as a dictionary, or None if not found
        """
        try:
            result = self.databases.get_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                document_id=message_id
            )
            return result
        except AppwriteException as e:
            if e.code == 404:
                return None
            logger.error(f"Failed to get scheduled message {message_id}: {e}")
            raise
    
    async def list_scheduled_messages_for_user(
        self,
        discord_user_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List scheduled messages for a specific user.
        
        Args:
            discord_user_id: The Discord user ID
            status: Optional status filter ('pending', 'sent', 'failed', 'cancelled')
            limit: Maximum number of messages to return
            
        Returns:
            List of scheduled message documents
        """
        try:
            queries = [
                Query.equal('discord_user_id', [discord_user_id]),
                Query.order_desc('scheduled_time'),
                Query.limit(limit)
            ]
            
            if status:
                queries.append(Query.equal('status', [status]))
            
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                queries=queries
            )
            
            return result['documents']
            
        except AppwriteException as e:
            logger.error(f"Failed to list scheduled messages for user {discord_user_id}: {e}")
            raise
    
    async def get_pending_messages(self, current_time: datetime) -> List[Dict[str, Any]]:
        """
        Get all pending messages that are due to be sent.
        
        Args:
            current_time: Current datetime to compare against scheduled_time
            
        Returns:
            List of pending message documents that are due
        """
        try:
            queries = [
                Query.equal('status', ['pending']),
                Query.less_than_equal('scheduled_time', current_time.isoformat()),
                Query.limit(100)  # Process in batches
            ]
            
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                queries=queries
            )
            
            return result['documents']
            
        except AppwriteException as e:
            logger.error(f"Failed to get pending messages: {e}")
            raise
    
    async def update_scheduled_message(
        self,
        message_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update a scheduled message with new data.
        
        Args:
            message_id: The Appwrite document ID
            **updates: Key-value pairs of fields to update
            
        Returns:
            The updated document
            
        Raises:
            AppwriteException: If the update fails
        """
        try:
            result = self.databases.update_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                document_id=message_id,
                data=updates
            )
            
            logger.info(f"Updated scheduled message {message_id}")
            return result
            
        except AppwriteException as e:
            logger.error(f"Failed to update scheduled message {message_id}: {e}")
            raise
    
    async def mark_message_as_sent(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a scheduled message as sent.
        
        Args:
            message_id: The Appwrite document ID
            
        Returns:
            The updated document
        """
        return await self.update_scheduled_message(
            message_id,
            status="sent",
            executed_at=datetime.utcnow().isoformat()
        )
    
    async def mark_message_as_failed(
        self,
        message_id: str,
        error_message: str,
        retry_count: int
    ) -> Dict[str, Any]:
        """
        Mark a scheduled message as failed.
        
        Args:
            message_id: The Appwrite document ID
            error_message: Description of the error
            retry_count: Current retry count
            
        Returns:
            The updated document
        """
        updates = {
            "error_message": error_message,
            "retry_count": retry_count
        }
        
        # Mark as failed if max retries reached
        if retry_count >= config.MAX_RETRY_ATTEMPTS:
            updates["status"] = "failed"
            updates["executed_at"] = datetime.utcnow().isoformat()
        
        return await self.update_scheduled_message(message_id, **updates)
    
    async def cancel_scheduled_message(self, message_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled message.
        
        Args:
            message_id: The Appwrite document ID
            
        Returns:
            The updated document
        """
        return await self.update_scheduled_message(
            message_id,
            status="cancelled"
        )
    
    async def delete_scheduled_message(self, message_id: str) -> bool:
        """
        Permanently delete a scheduled message.
        
        Args:
            message_id: The Appwrite document ID
            
        Returns:
            True if successful
            
        Raises:
            AppwriteException: If the deletion fails
        """
        try:
            self.databases.delete_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_SCHEDULED_MESSAGES,
                document_id=message_id
            )
            
            logger.info(f"Deleted scheduled message {message_id}")
            return True
            
        except AppwriteException as e:
            logger.error(f"Failed to delete scheduled message {message_id}: {e}")
            raise
    
    # ==================== User Preferences ====================
    
    async def get_user_preferences(self, discord_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences. Creates default preferences if not found.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            User preferences document
        """
        try:
            # Try to find existing preferences
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=config.COLLECTION_USER_PREFERENCES,
                queries=[
                    Query.equal('discord_user_id', [discord_user_id]),
                    Query.limit(1)
                ]
            )
            
            if result['documents']:
                return result['documents'][0]
            
            # Create default preferences if not found
            return await self.create_user_preferences(discord_user_id)
            
        except AppwriteException as e:
            logger.error(f"Failed to get user preferences for {discord_user_id}: {e}")
            raise
    
    async def create_user_preferences(
        self,
        discord_user_id: str,
        timezone: str = "UTC",
        max_scheduled_messages: int = 10,
        notification_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Create default user preferences.
        
        Args:
            discord_user_id: Discord user ID
            timezone: User's preferred timezone (default: UTC)
            max_scheduled_messages: Max concurrent scheduled messages
            notification_enabled: Whether to send notifications
            
        Returns:
            The created preferences document
        """
        try:
            now = datetime.utcnow().isoformat()
            document = {
                "discord_user_id": discord_user_id,
                "timezone": timezone,
                "max_scheduled_messages": max_scheduled_messages,
                "notification_enabled": notification_enabled,
                "created_at": now,
                "updated_at": now
            }
            
            result = self.databases.create_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_USER_PREFERENCES,
                document_id='unique()',
                data=document
            )
            
            logger.info(f"Created preferences for user {discord_user_id}")
            return result
            
        except AppwriteException as e:
            logger.error(f"Failed to create user preferences: {e}")
            raise
    
    async def update_user_preferences(
        self,
        discord_user_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update user preferences.
        
        Args:
            discord_user_id: Discord user ID
            **updates: Fields to update
            
        Returns:
            Updated preferences document
        """
        try:
            # Get existing preferences
            prefs = await self.get_user_preferences(discord_user_id)
            
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.databases.update_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_USER_PREFERENCES,
                document_id=prefs['$id'],
                data=updates
            )
            
            logger.info(f"Updated preferences for user {discord_user_id}")
            return result
            
        except AppwriteException as e:
            logger.error(f"Failed to update user preferences: {e}")
            raise
    
    # ==================== Execution Logs ====================
    
    async def create_execution_log(
        self,
        scheduled_message_id: str,
        discord_user_id: str,
        target_type: str,
        target_id: str,
        status: str,
        error_message: Optional[str] = None,
        message_preview: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an execution log entry.
        
        Args:
            scheduled_message_id: Reference to scheduled message document
            discord_user_id: User who scheduled the message
            target_type: Type of target (channel/dm/thread)
            target_id: Target Discord ID
            status: Execution status ('success', 'failed', 'retrying')
            error_message: Optional error description
            message_preview: Optional first 200 chars of message
            
        Returns:
            The created log document
        """
        try:
            document = {
                "scheduled_message_id": scheduled_message_id,
                "discord_user_id": discord_user_id,
                "execution_time": datetime.utcnow().isoformat(),
                "status": status,
                "target_type": target_type,
                "target_id": target_id
            }
            
            if error_message:
                document["error_message"] = error_message[:2000]  # Truncate if needed
            if message_preview:
                document["message_preview"] = message_preview[:200]
            
            result = self.databases.create_document(
                database_id=self.database_id,
                collection_id=config.COLLECTION_EXECUTION_LOGS,
                document_id='unique()',
                data=document
            )
            
            logger.info(f"Created execution log for message {scheduled_message_id}")
            return result
            
        except AppwriteException as e:
            logger.error(f"Failed to create execution log: {e}")
            # Don't raise - logging failures shouldn't stop execution
            return {}
    
    async def get_execution_logs_for_message(
        self,
        scheduled_message_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all execution logs for a specific scheduled message.
        
        Args:
            scheduled_message_id: The scheduled message document ID
            
        Returns:
            List of execution log documents
        """
        try:
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=config.COLLECTION_EXECUTION_LOGS,
                queries=[
                    Query.equal('scheduled_message_id', [scheduled_message_id]),
                    Query.order_desc('execution_time')
                ]
            )
            
            return result['documents']
            
        except AppwriteException as e:
            logger.error(f"Failed to get execution logs: {e}")
            raise

