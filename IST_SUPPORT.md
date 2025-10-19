# IST (Indian Standard Time) Support Guide

## ✅ IST is Already Supported!

The bot supports **all timezones** including IST. You just need to configure it.

---

## Quick Setup - Set IST as Your Timezone

### Method 1: Use the Discord Command (Per User)

In Discord, run:

```
/set_timezone timezone: Asia/Kolkata
```

This sets IST for your account. Now when you schedule messages:

```
/schedule_message
  channel: #general
  message: Good morning India! 🇮🇳
  time: tomorrow at 9am
```

The time "9am" will be interpreted as **9:00 AM IST**, not UTC!

---

## Default Timezone Changed to IST

### Changes Made

I've updated the default timezone from UTC to IST in two files:

#### 1. `appwrite_client.py`

```python
# Changed from:
timezone: str = "UTC"

# To:
timezone: str = "Asia/Kolkata"  # IST default
```

#### 2. `setup_appwrite.py`

```python
# Changed from:
"default": "UTC"

# To:
"default": "Asia/Kolkata"  # IST default
```

### What This Means:

- **New users** will automatically get IST as their timezone
- **Existing users** keep their current timezone (run `/set_timezone` to change)
- All time parsing uses IST by default for new users

---

## How to Apply the Changes

### If Running Locally:

```bash
# Just restart the bot
python bot.py
```

### If Running in Docker:

```bash
# Rebuild and restart
./rebuild.sh

# Or manually:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Using IST - Examples

### Schedule with IST Time

```
/schedule_message
  channel: #announcements
  message: Daily standup in 5 minutes!
  time: tomorrow at 10:30am
```

This schedules for **10:30 AM IST** (5:00 AM UTC)

### Relative Time (Works in Any Timezone)

```
/schedule_message
  channel: #general
  message: Lunch break!
  time: in 3 hours
```

Works the same regardless of timezone.

### Specific IST Date/Time

```
/schedule_message
  channel: #events
  message: Republic Day celebration! 🇮🇳
  time: 2026-01-26 10:00
```

This is **January 26, 2026 at 10:00 AM IST**

---

## Check Your Current Timezone

Run this command:

```
/preferences
```

You'll see your current settings including timezone.

---

## Supported Timezone Formats

All of these work for IST:

✅ **Recommended:**

- `Asia/Kolkata` - Official IANA timezone name (most accurate)
- `Asia/Calcutta` - Alternative name (same as Kolkata)

❌ **Not recommended:**

- `IST` - Ambiguous (could be Irish Standard Time or Israel Standard Time)

---

## Common Indian Timezones

| Location    | Timezone Identifier               |
| ----------- | --------------------------------- |
| India (IST) | `Asia/Kolkata` or `Asia/Calcutta` |
| Sri Lanka   | `Asia/Colombo`                    |
| Bangladesh  | `Asia/Dhaka`                      |
| Pakistan    | `Asia/Karachi`                    |
| Nepal       | `Asia/Kathmandu`                  |

---

## Update Existing User to IST

If you already have a preferences record with UTC, update it:

```
/set_timezone timezone: Asia/Kolkata
```

Or update preferences:

```
/update_preferences timezone: Asia/Kolkata
```

---

## Verify IST is Working

### Test 1: Schedule a Message

```
/schedule_message
  channel: #test
  message: IST test message
  time: in 1 minute
```

Check the confirmation - it should show the time in IST.

### Test 2: Check Preferences

```
/preferences
```

Should show:

```
Timezone: Asia/Kolkata
```

### Test 3: List Scheduled Messages

```
/list_scheduled
```

Times should be displayed in IST.

---

## Time Conversion Reference

IST is **UTC+5:30** (5 hours 30 minutes ahead of UTC)

| IST Time     | UTC Time                   |
| ------------ | -------------------------- |
| 12:00 AM IST | 6:30 PM UTC (previous day) |
| 6:00 AM IST  | 12:30 AM UTC               |
| 12:00 PM IST | 6:30 AM UTC                |
| 6:00 PM IST  | 12:30 PM UTC               |
| 11:59 PM IST | 6:29 PM UTC                |

---

## Troubleshooting

### "Time is in the past"

Make sure you're using the correct format:

```
# ✅ Good
time: tomorrow at 9am
time: 2025-10-20 14:30
time: in 2 hours

# ❌ Bad (if current IST time is past this)
time: 2025-10-18 08:00
```

### "Could not parse time"

Use one of these formats:

- `tomorrow at 3pm`
- `2025-12-25 14:30`
- `in 5 minutes`
- `next monday at 9am`

### "Wrong time zone"

Double-check your timezone:

```
/preferences
```

Update if needed:

```
/set_timezone timezone: Asia/Kolkata
```

---

## Other Popular Timezones (For Reference)

```
# US Timezones
/set_timezone timezone: America/New_York    # EST/EDT
/set_timezone timezone: America/Chicago     # CST/CDT
/set_timezone timezone: America/Denver      # MST/MDT
/set_timezone timezone: America/Los_Angeles # PST/PDT

# European Timezones
/set_timezone timezone: Europe/London       # GMT/BST
/set_timezone timezone: Europe/Paris        # CET/CEST
/set_timezone timezone: Europe/Berlin       # CET/CEST

# Asian Timezones
/set_timezone timezone: Asia/Tokyo          # JST
/set_timezone timezone: Asia/Shanghai       # CST
/set_timezone timezone: Asia/Singapore      # SGT
/set_timezone timezone: Asia/Dubai          # GST

# Australian Timezones
/set_timezone timezone: Australia/Sydney    # AEDT/AEST
/set_timezone timezone: Australia/Melbourne # AEDT/AEST
```

[Full timezone list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

---

## Code Changes Summary

### Files Modified:

1. ✅ `appwrite_client.py` - Default timezone changed to `Asia/Kolkata`
2. ✅ `setup_appwrite.py` - Database default changed to `Asia/Kolkata`

### Impact:

- **New users**: Automatically get IST
- **Existing users**: Keep current timezone (can update manually)
- **All scheduling**: Respects user's configured timezone

### No Breaking Changes:

- Users can still set any timezone they want
- Existing scheduled messages are not affected
- UTC still works if users prefer it

---

## Next Steps

1. **Rebuild if using Docker:**

   ```bash
   ./rebuild.sh
   ```

2. **Test the timezone:**

   ```
   /set_timezone timezone: Asia/Kolkata
   /preferences
   ```

3. **Schedule a test message:**

   ```
   /schedule_message channel: #test message: "IST test" time: in 2 minutes
   ```

4. **Verify the time** in the confirmation matches IST

---

## Pro Tips

1. **Use natural language for better readability:**

   - ✅ `tomorrow at 9am` (clear, timezone-aware)
   - ⚠️ `2025-10-20 09:00` (works, but timezone assumed)

2. **For critical times, verify in confirmation:**

   - Bot shows: "Scheduled Time: 2025-10-20 09:00 UTC"
   - Check if this matches your intended IST time

3. **Use relative times when possible:**

   - `in 30 minutes` works universally
   - No timezone confusion

4. **Check before scheduling:**
   ```
   /preferences  # Verify your timezone first
   ```

---

**IST is now the default timezone! 🇮🇳**

All new users will automatically use Indian Standard Time for scheduling messages.
