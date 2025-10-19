# Discord Message Scheduler Bot - User Guide

## Quick Start

The Discord Message Scheduler Bot allows you to schedule messages to be sent automatically at a specific time to channels, threads, or direct messages.

---

## 📅 Scheduling Commands

### 1. Schedule a Message to a Channel

Use the `/schedule_message` command to schedule a message to any text channel or thread.

**Command Syntax:**

```
/schedule_message
  channel: #channel-name
  message: Your message content here
  time: when to send the message
  thread: (optional) specific thread
```

**Examples:**

**Schedule for a specific date and time:**

```
/schedule_message
  channel: #general
  message: Don't forget about the team meeting!
  time: 2025-10-20 14:30
```

**Schedule using relative time:**

```
/schedule_message
  channel: #announcements
  message: The event starts in 1 hour!
  time: in 1 hour
```

**Schedule using natural language:**

```
/schedule_message
  channel: #general
  message: Happy Friday everyone!
  time: tomorrow at 9am
```

**Schedule to a thread:**

```
/schedule_message
  channel: #development
  message: Status update: Feature complete!
  time: in 30 minutes
  thread: Project Alpha Thread
```

---

### 2. Schedule a Direct Message (DM)

Use the `/schedule_dm` command to schedule a direct message to a user.

**Command Syntax:**

```
/schedule_dm
  user: @username
  message: Your message content here
  time: when to send
```

**Examples:**

**Birthday message:**

```
/schedule_dm
  user: @john
  message: Happy Birthday! 🎉
  time: 2025-10-25 08:00
```

**Reminder:**

```
/schedule_dm
  user: @sarah
  message: Don't forget to submit the report today!
  time: tomorrow at 10am
```

**Quick reminder:**

```
/schedule_dm
  user: @mike
  message: Meeting in 15 minutes!
  time: in 15 minutes
```

---

## ⏰ Time Format Options

The bot supports multiple time formats:

### Absolute Time (Specific Date/Time)

- `2025-10-20 14:30` - Date and time (24-hour format)
- `2025-10-20 2:30 PM` - Date and time (12-hour format)
- `10-20-2025 14:30` - Alternative date format

### Relative Time

- `in 5 minutes` - 5 minutes from now
- `in 2 hours` - 2 hours from now
- `in 3 days` - 3 days from now

### Natural Language

- `tomorrow at 3pm` - Tomorrow at 3 PM
- `next friday at 10am` - Next Friday at 10 AM
- `monday at 9:30am` - Next Monday at 9:30 AM

**Important:** All times are processed according to your timezone setting (default is UTC). Set your timezone with `/set_timezone` for accurate scheduling.

---

## 📋 Managing Scheduled Messages

### 3. List Your Scheduled Messages

View all your scheduled messages with `/list_scheduled`.

**Command Syntax:**

```
/list_scheduled
  status: (optional) pending, sent, failed, or cancelled
```

**Examples:**

**List all pending messages:**

```
/list_scheduled
  status: pending
```

**List all messages (any status):**

```
/list_scheduled
```

**List sent messages:**

```
/list_scheduled
  status: sent
```

**What you'll see:**

- Message ID
- Target (channel/user)
- Scheduled time
- Message preview
- Current status

---

### 4. Cancel a Scheduled Message

Cancel a pending message before it's sent with `/cancel_scheduled`.

**Command Syntax:**

```
/cancel_scheduled
  message_id: paste-the-message-id-here
```

**Example:**

```
/cancel_scheduled
  message_id: 67123abc456def
```

**Note:**

- You can only cancel messages with status "pending"
- Get the message ID from `/list_scheduled`
- You can only cancel your own messages

---

### 5. Edit a Scheduled Message

Modify the time or content of a pending message with `/edit_scheduled`.

**Command Syntax:**

```
/edit_scheduled
  message_id: the-message-id
  new_time: (optional) new time to send
  new_message: (optional) new message content
```

**Examples:**

**Change the scheduled time:**

```
/edit_scheduled
  message_id: 67123abc456def
  new_time: tomorrow at 5pm
```

**Change the message content:**

```
/edit_scheduled
  message_id: 67123abc456def
  new_message: Updated announcement text here
```

**Change both time and content:**

```
/edit_scheduled
  message_id: 67123abc456def
  new_time: in 3 hours
  new_message: This is the updated message
```

**Note:** You must provide at least one of `new_time` or `new_message`

---

## ⚙️ Settings & Preferences

### 6. Set Your Timezone

Configure your timezone for accurate time parsing with `/set_timezone`.

**Command Syntax:**

```
/set_timezone
  timezone: your timezone (e.g., America/New_York)
```

**Examples:**

```
/set_timezone timezone: America/New_York
/set_timezone timezone: Europe/London
/set_timezone timezone: Asia/Tokyo
/set_timezone timezone: Australia/Sydney
/set_timezone timezone: America/Los_Angeles
```

**Common Timezones:**

- `UTC` - Coordinated Universal Time
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `Europe/London` - British Time
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan Time
- `Australia/Sydney` - Australian Eastern Time

[Full list of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

---

### 7. View Your Preferences

Check your current settings with `/preferences`.

**Command Syntax:**

```
/preferences
```

**What you'll see:**

- Your timezone setting
- Maximum allowed scheduled messages
- Notification preferences
- Total pending messages

---

### 8. Update Preferences

Modify your bot preferences with `/update_preferences`.

**Command Syntax:**

```
/update_preferences
  max_messages: (optional) maximum pending messages (1-50)
  notifications: (optional) enable/disable notifications
```

**Examples:**

**Increase your message limit:**

```
/update_preferences
  max_messages: 25
```

**Disable notifications:**

```
/update_preferences
  notifications: False
```

**Update both:**

```
/update_preferences
  max_messages: 20
  notifications: True
```

---

### 9. Get Help

Display help information with `/help`.

**Command Syntax:**

```
/help
```

Shows all available commands and their descriptions.

---

## 🔔 Notifications

When notifications are enabled, you'll receive a DM from the bot when:

### ✅ Message Sent Successfully

You'll get a notification with:

- Confirmation that the message was sent
- Message ID
- Content preview

### ❌ Message Failed

You'll get a notification with:

- Error description
- Message ID
- Content preview

**Disable notifications:**

```
/update_preferences notifications: False
```

---

## 📊 Message Status Types

- **pending** 🟡 - Scheduled, waiting to be sent
- **sent** ✅ - Successfully delivered
- **failed** ❌ - Delivery failed (after retries)
- **cancelled** 🚫 - Cancelled by user

---

## ⚠️ Important Notes

### Permissions Required

- The bot needs "Send Messages" permission in target channels
- The bot cannot send DMs to users who have DMs disabled
- You need appropriate permissions to schedule to a channel

### Limitations

- Default limit: 10 pending messages per user (adjustable)
- Messages cannot be scheduled in the past
- Scheduled time must be in the future
- Cannot schedule messages to bots
- Cannot schedule messages to yourself (DMs)

### Retry Logic

- If a message fails to send, the bot will retry up to 3 times
- After 3 failed attempts, the message is marked as "failed"
- Permission errors and "not found" errors are not retried

### Scheduler Check Interval

- The bot checks for pending messages every 60 seconds (configurable)
- Messages may be sent up to 60 seconds after the scheduled time
- For time-critical messages, consider scheduling slightly earlier

---

## 💡 Use Cases & Examples

### Daily Standup Reminder

```
/schedule_message
  channel: #team
  message: @everyone Daily standup in 5 minutes!
  time: tomorrow at 9:55am
```

### Weekly Team Meeting

```
/schedule_message
  channel: #general
  message: Weekly team meeting starting now! Join the call.
  time: next monday at 2pm
```

### Event Countdown

```
/schedule_message
  channel: #announcements
  message: 🎉 Product launch in 24 hours! Get ready!
  time: 2025-10-24 12:00
```

### Personal Reminder

```
/schedule_dm
  user: @me
  message: Time to take a break and stretch!
  time: in 2 hours
```

### Deadline Alert

```
/schedule_message
  channel: #project-alpha
  message: ⚠️ Deadline is tomorrow! Please submit your work.
  time: today at 5pm
```

---

## 🆘 Troubleshooting

### "I don't have permission to send messages in that channel"

- Make sure the bot has "Send Messages" permission in the target channel
- Check channel-specific permissions

### "Could not parse time"

- Use one of the supported time formats (see Time Format Options above)
- Make sure the time is in the future
- Check your timezone setting with `/preferences`

### "You've reached your limit of pending messages"

- Cancel some pending messages with `/cancel_scheduled`
- Wait for scheduled messages to be sent
- Increase your limit with `/update_preferences`

### "Message not found"

- Make sure you're using the correct message ID
- The message may have already been sent or cancelled
- Use `/list_scheduled` to get current message IDs

### "Cannot send DM to this user"

- The user may have DMs disabled
- You cannot DM bots
- Check if the user is still in the server

---

## 🎯 Best Practices

1. **Set your timezone first** - Use `/set_timezone` for accurate scheduling
2. **Test with short intervals** - Try "in 1 minute" before scheduling hours ahead
3. **Check your messages** - Use `/list_scheduled` to verify your scheduled messages
4. **Use clear message IDs** - Copy the entire message ID when canceling/editing
5. **Enable notifications** - Stay informed about message delivery status
6. **Plan ahead** - Schedule messages well before important events
7. **Double-check times** - Verify the scheduled time in the confirmation message

---

## 📞 Support

If you encounter issues:

1. Check this user guide
2. Use `/help` for quick command reference
3. Verify your timezone settings with `/preferences`
4. Check bot permissions in the target channel
5. Contact your server administrator or bot owner

---

## 🎉 Quick Reference Card

| Command               | Purpose                    | Example                                                     |
| --------------------- | -------------------------- | ----------------------------------------------------------- |
| `/schedule_message`   | Schedule to channel/thread | `/schedule_message #general "Hello" "tomorrow at 3pm"`      |
| `/schedule_dm`        | Schedule DM to user        | `/schedule_dm @john "Reminder" "in 1 hour"`                 |
| `/list_scheduled`     | View scheduled messages    | `/list_scheduled status: pending`                           |
| `/cancel_scheduled`   | Cancel a message           | `/cancel_scheduled message_id: 123abc`                      |
| `/edit_scheduled`     | Edit time or content       | `/edit_scheduled message_id: 123abc new_time: "in 2 hours"` |
| `/set_timezone`       | Set your timezone          | `/set_timezone timezone: America/New_York`                  |
| `/preferences`        | View your settings         | `/preferences`                                              |
| `/update_preferences` | Change settings            | `/update_preferences max_messages: 20`                      |
| `/help`               | Show help                  | `/help`                                                     |

---

**Happy Scheduling! 🚀**
