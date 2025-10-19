#!/usr/bin/env python3
"""
Appwrite Database Setup Script for SDK v13.x

This script initializes the Appwrite database with the required collections
and attributes for the Discord Message Scheduler bot.

Updated for Appwrite SDK 13.x compatibility.

Usage:
    python setup_appwrite.py
"""

import os
import sys
import traceback
import time
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DATABASE_ID = "discord_scheduler_db"
COLLECTIONS = {
    "scheduled_messages": {
        "name": "Scheduled Messages",
        "attributes": [
            {"key": "discord_user_id", "type": "string", "size": 255, "required": True},
            {"key": "target_type", "type": "string", "size": 50, "required": True},
            {"key": "target_id", "type": "string", "size": 255, "required": True},
            {"key": "message_content", "type": "string", "size": 4000, "required": True},
            {"key": "scheduled_time", "type": "datetime", "required": True},
            {"key": "status", "type": "string", "size": 50, "required": False, "default": "pending"},
            {"key": "created_at", "type": "datetime", "required": True},
            {"key": "executed_at", "type": "datetime", "required": False},
            {"key": "error_message", "type": "string", "size": 1000, "required": False},
            {"key": "retry_count", "type": "integer", "required": False, "default": 0, "min": 0, "max": 5},
            {"key": "guild_id", "type": "string", "size": 255, "required": False},
            {"key": "thread_id", "type": "string", "size": 255, "required": False},
        ],
        "indexes": [
            {"key": "idx_status", "type": "key", "attributes": ["status"]},
            {"key": "idx_scheduled_time", "type": "key", "attributes": ["scheduled_time"]},
            {"key": "idx_discord_user_id", "type": "key", "attributes": ["discord_user_id"]},
            {"key": "idx_status_scheduled_time", "type": "key", "attributes": ["status", "scheduled_time"]},
        ]
    },
    "user_preferences": {
        "name": "User Preferences",
        "attributes": [
            {"key": "discord_user_id", "type": "string", "size": 255, "required": True},
            {"key": "timezone", "type": "string", "size": 100, "required": False, "default": "UTC"},
            {"key": "max_scheduled_messages", "type": "integer", "required": False, "default": 10, "min": 1, "max": 50},
            {"key": "notification_enabled", "type": "boolean", "required": False, "default": True},
            {"key": "created_at", "type": "datetime", "required": True},
            {"key": "updated_at", "type": "datetime", "required": True},
        ],
        "indexes": [
            {"key": "idx_discord_user_id", "type": "unique", "attributes": ["discord_user_id"]},
        ]
    },
    "execution_logs": {
        "name": "Execution Logs",
        "attributes": [
            {"key": "scheduled_message_id", "type": "string", "size": 255, "required": True},
            {"key": "discord_user_id", "type": "string", "size": 255, "required": True},
            {"key": "execution_time", "type": "datetime", "required": True},
            {"key": "status", "type": "string", "size": 50, "required": True},
            {"key": "error_message", "type": "string", "size": 2000, "required": False},
            {"key": "target_type", "type": "string", "size": 50, "required": True},
            {"key": "target_id", "type": "string", "size": 255, "required": True},
            {"key": "message_preview", "type": "string", "size": 200, "required": False},
        ],
        "indexes": [
            {"key": "idx_scheduled_message_id", "type": "key", "attributes": ["scheduled_message_id"]},
            {"key": "idx_discord_user_id", "type": "key", "attributes": ["discord_user_id"]},
            {"key": "idx_execution_time", "type": "key", "attributes": ["execution_time"]},
        ]
    }
}


def get_client():
    """Initialize and return Appwrite client."""
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    api_key = os.getenv("APPWRITE_API_KEY")

    if not all([endpoint, project_id, api_key]):
        print("❌ Error: Missing required environment variables")
        print("   Required: APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY")
        sys.exit(1)

    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    return client

def create_database(databases):
    """Create the main database if it doesn't exist."""
    try:
        dbs = databases.list()
        if any(d["$id"] == DATABASE_ID for d in dbs["databases"]):
            print(f"✅ Database '{DATABASE_ID}' already exists")
            return True
    except AppwriteException as e:
        print(f"⚠️  Warning: Could not list databases ({e.message})")

    # If not found, create the database
    try:
        databases.create(
            database_id=DATABASE_ID,
            name="Discord Scheduler Database"
        )
        print(f"✅ Created database '{DATABASE_ID}'")
        return True
    except AppwriteException as create_error:
        print(traceback.format_exc())
        print(f"❌ Error creating database: {create_error.message}")
        return False

def collection_exists(databases, collection_id):
    """Check if a collection exists."""
    try:
        collections = databases.list_collections(DATABASE_ID)
        for c in collections.get("collections", []):
            if c["$id"] == collection_id:
                return True
    except AppwriteException as e:
        print(f"⚠️  Warning: Could not list collections ({e.message})")
    return False


def get_collection_attributes(databases, collection_id):
    """Get existing attributes from a collection."""
    try:
        collection = databases.get_collection(
            database_id=DATABASE_ID,
            collection_id=collection_id
        )
        return [attr["key"] for attr in collection.get("attributes", [])]
    except AppwriteException:
        return []


def create_collection(databases, collection_id, collection_data):
    """Create a collection with its attributes and indexes."""
    collection_existed = collection_exists(databases, collection_id)
    
    if collection_existed:
        print(f"✅ Collection '{collection_id}' already exists")
    else:
        # Create collection
        try:
            databases.create_collection(
                database_id=DATABASE_ID,
                collection_id=collection_id,
                name=collection_data["name"],
                document_security=True
            )
            print(f"✅ Created collection '{collection_id}'")
        except AppwriteException as create_error:
            print(f"❌ Error creating collection '{collection_id}': {create_error.message}")
            return False

    # Get existing attributes
    existing_attrs = get_collection_attributes(databases, collection_id)
    
    # Create missing attributes
    for attr in collection_data["attributes"]:
        key = attr["key"]
        
        if key in existing_attrs:
            print(f"  ⏭️  Attribute '{key}' already exists, skipping")
            continue
            
        try:
            t = attr["type"]

            if t == "string":
                databases.create_string_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=key,
                    size=attr["size"],
                    required=attr["required"],
                    default=attr.get("default")
                )
            elif t == "integer":
                databases.create_integer_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=key,
                    required=attr["required"],
                    min=attr.get("min"),
                    max=attr.get("max"),
                    default=attr.get("default")
                )
            elif t == "boolean":
                databases.create_boolean_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=key,
                    required=attr["required"],
                    default=attr.get("default")
                )
            elif t == "datetime":
                databases.create_datetime_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=key,
                    required=attr["required"],
                    default=attr.get("default")
                )

            print(f"  ✅ Created attribute '{key}'")

        except AppwriteException as attr_error:
            print(f"  ⚠️  Error creating attribute '{key}': {attr_error.message}")

    if not collection_existed or len([a for a in collection_data["attributes"] if a["key"] not in existing_attrs]) > 0:
        print("  ⏳ Waiting for attributes to be ready...")
        time.sleep(3)

    # Create indexes
    for index in collection_data["indexes"]:
        try:
            databases.create_index(
                database_id=DATABASE_ID,
                collection_id=collection_id,
                key=index["key"],
                type=index["type"],
                attributes=index["attributes"],
                orders=["ASC"] * len(index["attributes"])
            )
            print(f"  ✅ Created index '{index['key']}'")
        except AppwriteException as index_error:
            # Index might already exist, which is fine
            if "already exists" in str(index_error.message).lower() or "index with the requested id already exists" in str(index_error.message).lower():
                print(f"  ⏭️  Index '{index['key']}' already exists, skipping")
            else:
                print(f"  ⚠️  Error creating index '{index['key']}': {index_error.message}")

    return True


def main():
    """Main setup function."""
    print("\n🚀 Discord Message Scheduler - Appwrite Setup")
    print("=" * 50)

    print("\n📡 Connecting to Appwrite...")
    client = get_client()
    databases = Databases(client)

    print(f"\n📁 Setting up database...")
    if not create_database(databases):
        sys.exit(1)

    print(f"\n📦 Creating collections...")
    for collection_id, collection_data in COLLECTIONS.items():
        print(f"\n  Collection: {collection_id}")
        if not create_collection(databases, collection_id, collection_data):
            print(f"  ⚠️  Warning: Collection '{collection_id}' setup incomplete")

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📝 Next steps:")
    print("  1. Configure your Discord bot token in .env file")
    print("  2. Update APPWRITE_DATABASE_ID in your bot configuration")
    print("  3. Run the bot: python bot.py\n")


if __name__ == "__main__":
    main()

