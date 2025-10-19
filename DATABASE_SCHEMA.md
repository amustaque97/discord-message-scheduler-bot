# Database Schema Documentation

## Overview

This document describes the Appwrite database schema for the Discord Message Scheduler bot.

## Database: `discord_scheduler_db`

### Collections

---

## 1. Scheduled Messages (`scheduled_messages`)

Stores all scheduled messages with their metadata and execution status.

### Attributes

| Field             | Type     | Size | Required | Description                                              |
| ----------------- | -------- | ---- | -------- | -------------------------------------------------------- |
| `discord_user_id` | string   | 255  | Yes      | Discord user ID who scheduled the message                |
| `target_type`     | string   | 50   | Yes      | Type of target: 'channel', 'dm', or 'thread'             |
| `target_id`       | string   | 255  | Yes      | Discord ID of the target (channel, user, or thread)      |
| `message_content` | string   | 4000 | Yes      | Content of the message to be sent                        |
| `scheduled_time`  | datetime | -    | Yes      | UTC timestamp when the message should be sent            |
| `status`          | string   | 50   | Yes      | Message status: 'pending', 'sent', 'failed', 'cancelled' |
| `created_at`      | datetime | -    | Yes      | Timestamp when the message was scheduled                 |
| `executed_at`     | datetime | -    | No       | Timestamp when the message was actually sent             |
| `error_message`   | string   | 1000 | No       | Error description if sending failed                      |
| `retry_count`     | integer  | -    | Yes      | Number of retry attempts (0-5)                           |
| `guild_id`        | string   | 255  | No       | Discord server/guild ID (if applicable)                  |
| `thread_id`       | string   | 255  | No       | Thread ID (if target is a thread)                        |

### Indexes

- `idx_status`: Index on status field for quick filtering
- `idx_scheduled_time`: Index on scheduled_time for efficient time-based queries
- `idx_discord_user_id`: Index on user ID for user-specific queries
- `idx_status_scheduled_time`: Composite index for querying pending messages by time

### Status Values

- `pending`: Message is scheduled but not yet sent
- `sent`: Message was successfully delivered
- `failed`: Message delivery failed after retries
- `cancelled`: Message was cancelled by user

### Target Types

- `channel`: Regular text channel in a server
- `dm`: Direct message to a user
- `thread`: Message in a thread (forum or regular)

---

## 2. User Preferences (`user_preferences`)

Stores user-specific settings and preferences.

### Attributes

| Field                    | Type     | Size | Required | Default | Description                                          |
| ------------------------ | -------- | ---- | -------- | ------- | ---------------------------------------------------- |
| `discord_user_id`        | string   | 255  | Yes      | -       | Discord user ID (unique)                             |
| `timezone`               | string   | 100  | Yes      | 'UTC'   | User's preferred timezone (e.g., 'America/New_York') |
| `max_scheduled_messages` | integer  | -    | Yes      | 10      | Maximum number of concurrent scheduled messages      |
| `notification_enabled`   | boolean  | -    | Yes      | true    | Whether to send confirmation notifications           |
| `created_at`             | datetime | -    | Yes      | -       | When the preferences were created                    |
| `updated_at`             | datetime | -    | Yes      | -       | Last update timestamp                                |

### Indexes

- `idx_discord_user_id`: Unique index ensuring one preference document per user

### Notes

- The `timezone` field uses IANA timezone database names (e.g., 'America/New_York', 'Europe/London')
- `max_scheduled_messages` helps prevent spam and abuse (configurable per user)
- Preferences are created automatically on first command usage

---

## 3. Execution Logs (`execution_logs`)

Records the execution history of scheduled messages for auditing and debugging.

### Attributes

| Field                  | Type     | Size | Required | Description                                       |
| ---------------------- | -------- | ---- | -------- | ------------------------------------------------- |
| `scheduled_message_id` | string   | 255  | Yes      | Reference to the scheduled message document ID    |
| `discord_user_id`      | string   | 255  | Yes      | User who scheduled the message                    |
| `execution_time`       | datetime | -    | Yes      | When the execution attempt was made               |
| `status`               | string   | 50   | Yes      | Execution result: 'success', 'failed', 'retrying' |
| `error_message`        | string   | 2000 | No       | Detailed error message if execution failed        |
| `target_type`          | string   | 50   | Yes      | Type of target (channel/dm/thread)                |
| `target_id`            | string   | 255  | Yes      | Target Discord ID                                 |
| `message_preview`      | string   | 200  | No       | First 200 characters of the message               |

### Indexes

- `idx_scheduled_message_id`: Index for looking up logs by message ID
- `idx_discord_user_id`: Index for user-specific log queries
- `idx_execution_time`: Descending index for chronological log retrieval

### Status Values

- `success`: Message was successfully delivered
- `failed`: Delivery attempt failed
- `retrying`: Failed but will retry

---

## Data Flow

1. **Scheduling**: User runs a command → Bot creates document in `scheduled_messages` with status='pending'
2. **Execution**: Scheduler checks for pending messages → Sends message → Updates status to 'sent' or 'failed' → Creates log in `execution_logs`
3. **Management**: User lists/edits/cancels → Bot queries/updates `scheduled_messages` collection
4. **Preferences**: Bot reads from `user_preferences` to respect user limits and timezone settings

---

## Security Considerations

- All collections use document-level security (`documentSecurity: true`)
- Permissions should be configured to ensure users can only access their own scheduled messages
- The bot uses an API key with appropriate permissions for all operations
- User IDs from Discord are validated before database operations

---

## Maintenance

### Cleanup Recommendations

- Archive or delete execution logs older than 30 days to manage database size
- Remove 'sent' messages older than 7 days if not needed for auditing
- Monitor 'failed' messages for patterns indicating bot issues

### Performance Optimization

- The composite index `idx_status_scheduled_time` optimizes the main scheduler query
- Consider adding indexes if filtering by guild_id becomes common
- Monitor query performance and adjust indexes as usage patterns emerge

