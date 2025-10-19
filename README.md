# Discord Message Scheduler Bot

A powerful Discord bot that allows users to schedule messages to channels, threads, and DMs using Appwrite as the backend database. Built with Python, discord.py, and Appwrite SDK.

## 🌟 Features

- **📅 Schedule Messages** - Schedule messages to channels, threads, or direct messages
- **⏰ Flexible Time Parsing** - Support for natural language ("tomorrow at 3pm"), relative time ("in 2 hours"), and absolute timestamps
- **🌍 Timezone Support** - Set your timezone for accurate scheduling
- **✏️ Message Management** - List, edit, and cancel scheduled messages
- **🔄 Retry Logic** - Automatic retry mechanism for failed messages
- **📊 Execution Logs** - Complete audit trail of all message deliveries
- **🔔 Notifications** - Optional notifications when messages are sent or fail
- **👥 User Preferences** - Customizable settings per user

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Bot](#running-the-bot)
- [Command Reference](#command-reference)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

- Python 3.9 or higher
- Discord Bot Account with appropriate permissions
- Appwrite instance (cloud or self-hosted)
- Appwrite project with API key

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd discord-bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Copy environment variables**

   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` file with your credentials**

   ```env
   # Discord Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_GUILD_ID=your_guild_id_for_testing  # Optional: for dev

   # Appwrite Configuration
   APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
   APPWRITE_PROJECT_ID=your_project_id_here
   APPWRITE_API_KEY=your_api_key_here
   APPWRITE_DATABASE_ID=discord_scheduler_db

   # Bot Configuration
   SCHEDULER_CHECK_INTERVAL=60  # Check every 60 seconds
   MAX_RETRY_ATTEMPTS=3
   LOG_LEVEL=INFO
   ```

## ⚙️ Configuration

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Enable the following **Privileged Gateway Intents**:
   - Message Content Intent
   - Server Members Intent (optional)
5. Copy the bot token to your `.env` file
6. Generate an invite URL:
   - Go to "OAuth2" > "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select bot permissions:
     - Send Messages
     - Send Messages in Threads
     - Read Message History
     - Use Slash Commands
   - Copy the generated URL and invite the bot to your server

### Appwrite Setup

1. Create an Appwrite account at [Appwrite Cloud](https://cloud.appwrite.io) or use self-hosted instance
2. Create a new project
3. Generate an API key with the following scopes:
   - `databases.read`
   - `databases.write`
   - `collections.read`
   - `collections.write`
   - `attributes.read`
   - `attributes.write`
   - `indexes.read`
   - `indexes.write`
   - `documents.read`
   - `documents.write`
4. Copy the project ID and API key to your `.env` file

## 🗄️ Database Setup

Run the setup script to create the required database collections:

```bash
python setup_appwrite.py
```

This script will:

- Create the `discord_scheduler_db` database
- Create three collections:
  - `scheduled_messages` - Stores all scheduled messages
  - `user_preferences` - Stores user settings
  - `execution_logs` - Stores execution history
- Create all required attributes and indexes

For detailed schema information, see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## 🚀 Running the Bot

### Development Mode

```bash
python bot.py
```

The bot will:

1. Validate configuration
2. Connect to Discord
3. Initialize Appwrite client
4. Sync slash commands (instantly if DISCORD_GUILD_ID is set)
5. Start the scheduler service

### Production Mode

For production, use a process manager like PM2, systemd, or Docker (see [Deployment Guide](#deployment)).

## 📚 Command Reference

### Scheduling Commands

#### `/schedule_message`

Schedule a message to be sent to a channel or thread.

**Parameters:**

- `channel` (required) - The target channel
- `message` (required) - Message content (up to 4000 characters)
- `time` (required) - When to send (see [Time Formats](#time-formats))
- `thread` (optional) - The thread to send to (if targeting a thread)

**Example:**

```
/schedule_message channel:#general message:"Hello, world!" time:"tomorrow at 3pm"
```

#### `/schedule_dm`

Schedule a direct message to be sent to a user.

**Parameters:**

- `user` (required) - The recipient user
- `message` (required) - Message content (up to 4000 characters)
- `time` (required) - When to send

**Example:**

```
/schedule_dm user:@John message:"Happy birthday!" time:"2024-12-25 09:00"
```

### Management Commands

#### `/list_scheduled`

List all your scheduled messages.

**Parameters:**

- `status` (optional) - Filter by status: `pending`, `sent`, `failed`, `cancelled`

**Example:**

```
/list_scheduled status:pending
```

#### `/edit_scheduled`

Edit a scheduled message's time or content.

**Parameters:**

- `message_id` (required) - The ID of the scheduled message
- `new_time` (optional) - New time to send the message
- `new_message` (optional) - New message content

**Note:** At least one of `new_time` or `new_message` must be provided.

**Example:**

```
/edit_scheduled message_id:abc123 new_time:"in 3 hours"
```

#### `/cancel_scheduled`

Cancel a pending scheduled message.

**Parameters:**

- `message_id` (required) - The ID of the scheduled message

**Example:**

```
/cancel_scheduled message_id:abc123
```

### Utility Commands

#### `/help`

Display help information about available commands.

#### `/set_timezone`

Set your timezone for scheduling messages.

**Parameters:**

- `timezone` (required) - IANA timezone name (e.g., `America/New_York`)

**Example:**

```
/set_timezone timezone:America/New_York
```

**Common Timezones:**

- `America/New_York` - Eastern Time (US)
- `America/Los_Angeles` - Pacific Time (US)
- `Europe/London` - UK
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan
- `Australia/Sydney` - Australian Eastern Time

Find more at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

#### `/preferences`

View and update your preferences.

**Parameters:**

- `notifications` (optional) - Enable/disable notifications (`true` or `false`)

**Example:**

```
/preferences notifications:false
```

### Time Formats

The bot supports multiple time formats:

1. **Absolute Date/Time**
   - `2024-12-25 14:30` - Specific date and time
   - `December 25, 2024 2:30pm` - Natural language date

2. **Relative Time**
   - `in 2 hours` - Relative to now
   - `in 30 minutes`
   - `in 3 days`

3. **Natural Language**
   - `tomorrow at 3pm`
   - `next friday at 10am`
   - `monday at noon`

**Note:** Times are interpreted in your configured timezone (default: UTC).

## 🏗️ Architecture

### Project Structure

```
discord-bot/
├── bot.py                      # Main bot entry point
├── config.py                   # Configuration management
├── appwrite_client.py          # Appwrite database wrapper
├── scheduler_service.py        # Background scheduler service
├── setup_appwrite.py           # Database setup script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── DATABASE_SCHEMA.md          # Database schema documentation
├── commands/                   # Command modules
│   ├── __init__.py
│   ├── schedule_commands.py    # Scheduling commands
│   ├── management_commands.py  # Management commands
│   └── utility_commands.py     # Utility commands
└── README.md                   # This file
```

### Components

#### Bot (`bot.py`)

- Main entry point
- Initializes Discord client with required intents
- Loads command cogs
- Manages bot lifecycle

#### Appwrite Client (`appwrite_client.py`)

- Wraps Appwrite SDK
- Provides typed helper functions for CRUD operations
- Handles database queries and updates
- Manages user preferences

#### Scheduler Service (`scheduler_service.py`)

- Background task that runs every N seconds (configurable)
- Queries for pending messages that are due
- Sends messages via Discord API
- Updates message status and creates execution logs
- Handles retries and error recovery
- Sends optional notifications to users

#### Command Cogs

- **Schedule Commands** - `/schedule_message`, `/schedule_dm`
- **Management Commands** - `/list_scheduled`, `/edit_scheduled`, `/cancel_scheduled`
- **Utility Commands** - `/help`, `/set_timezone`, `/preferences`

### Data Flow

1. **Scheduling**

   ```
   User runs /schedule_message
   → Command validates input
   → Creates document in scheduled_messages collection
   → Returns confirmation to user
   ```

2. **Execution**

   ```
   Scheduler service checks for due messages every N seconds
   → Finds pending messages where scheduled_time <= now
   → Attempts to send message via Discord
   → Updates message status (sent/failed)
   → Creates execution log
   → Sends notification to user (if enabled)
   ```

3. **Management**

   ```
   User runs /list_scheduled
   → Queries user's messages from database
   → Formats and displays results

   User runs /cancel_scheduled
   → Verifies ownership
   → Updates message status to cancelled
   → Returns confirmation
   ```

## 🚢 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions, including:

- Docker deployment
- Appwrite Functions deployment
- Systemd service setup
- PM2 configuration
- Environment variable management

## 🔍 Troubleshooting

### Bot doesn't respond to commands

1. **Check bot permissions:**
   - Ensure the bot has "Use Slash Commands" permission in your server
   - Verify the bot is online

2. **Verify command sync:**
   - If using `DISCORD_GUILD_ID`, commands sync instantly
   - Global commands can take up to 1 hour to sync
   - Check logs for sync confirmation

3. **Check logs:**
   ```bash
   tail -f bot.log
   ```

### Messages not being sent

1. **Check scheduler service:**
   - Verify scheduler service started (check logs)
   - Ensure `SCHEDULER_CHECK_INTERVAL` is set appropriately

2. **Check permissions:**
   - Bot needs "Send Messages" permission in target channels
   - Bot needs "Send Messages in Threads" for thread targets
   - Check execution logs for specific errors

3. **Database connectivity:**
   - Verify Appwrite credentials in `.env`
   - Check network connectivity to Appwrite instance

### Database errors

1. **Run setup script again:**

   ```bash
   python setup_appwrite.py
   ```

2. **Verify API key permissions:**
   - Ensure API key has all required scopes
   - Check that database ID matches configuration

3. **Check Appwrite instance:**
   - Verify Appwrite endpoint is accessible
   - Check Appwrite console for errors

## 📝 Logging

Logs are written to:

- Console (stdout)
- `bot.log` file

Log levels can be configured via `LOG_LEVEL` environment variable:

- `DEBUG` - Detailed information
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [discord.py](https://discordpy.readthedocs.io/)
- Backend powered by [Appwrite](https://appwrite.io/)
- Time parsing using [python-dateutil](https://dateutil.readthedocs.io/)

## 📧 Support

For questions or issues:

- Open an issue on GitHub
- Check existing documentation
- Review logs for error messages

---

Made with ❤️ using Python, Discord.py, and Appwrite

