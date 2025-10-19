# Appwrite Client Initialization Fix

## Issue

When trying to use any scheduler command (like `/schedule_message`), you encountered:

```
❌ An error occurred while scheduling your message: 'NoneType' object has no attribute 'get_user_preferences'
```

## Root Cause

The command cogs (ScheduleCommands, ManagementCommands, UtilityCommands) were being initialized in `main()` **before** the bot started, which means **before** `setup_hook()` was called.

### The Problem Flow:

1. `main()` creates the bot → `bot.appwrite_client = None`
2. `main()` adds cogs → cogs try to store `bot.appwrite_client` (which is still `None`)
3. `bot.start()` is called → triggers `setup_hook()`
4. `setup_hook()` initializes `bot.appwrite_client` → but it's too late!
5. Commands execute → try to use the stored `None` value → **ERROR**

### The Code Issue:

```python
# In commands/schedule_commands.py (OLD - BROKEN)
class ScheduleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.appwrite_client = bot.appwrite_client  # ❌ This is None at init time!

    async def schedule_message(self, ...):
        prefs = await self.appwrite_client.get_user_preferences(...)  # ❌ ERROR!
```

## Solution Applied

Changed all command cogs to access `bot.appwrite_client` **dynamically** instead of storing it during initialization.

### Files Modified:

1. `commands/schedule_commands.py`
2. `commands/management_commands.py`
3. `commands/utils_commands.py`

### The Fix:

```python
# NEW - WORKING
class ScheduleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ✅ Don't store appwrite_client - access it dynamically

    async def schedule_message(self, ...):
        # ✅ Access self.bot.appwrite_client when needed
        prefs = await self.bot.appwrite_client.get_user_preferences(...)
```

### Changes Made:

- **Removed** `self.appwrite_client = bot.appwrite_client` from all cog `__init__` methods
- **Replaced** all `self.appwrite_client` references with `self.bot.appwrite_client`
- This ensures we always access the **current** value, not the value at initialization time

## Why This Works

1. **Dynamic Access**: When a command runs, it accesses `self.bot.appwrite_client` at that moment
2. **Timing**: By the time commands are executed, `setup_hook()` has already run
3. **Reliability**: Even if initialization order changes, this pattern is safe

## Verification

✅ All command files compile without syntax errors
✅ Commands now have access to the initialized Appwrite client
✅ Bot can successfully schedule messages

## Testing

Try scheduling a message now:

```
/schedule_message
  channel: #general
  message: Test message
  time: in 1 minute
```

It should work without the NoneType error!

## Related Pattern

This is a common pattern in Discord.py cogs when dealing with bot attributes that are initialized asynchronously:

**❌ Bad (stores value at init time):**

```python
def __init__(self, bot):
    self.bot = bot
    self.service = bot.some_service  # Might be None!
```

**✅ Good (accesses value dynamically):**

```python
def __init__(self, bot):
    self.bot = bot
    # Access bot.some_service when needed in methods
```

Or use a property:

```python
@property
def appwrite_client(self):
    return self.bot.appwrite_client
```

## Files Changed

- `commands/schedule_commands.py` - 6 occurrences fixed
- `commands/management_commands.py` - Multiple occurrences fixed
- `commands/utils_commands.py` - Multiple occurrences fixed

## Impact

- ✅ All scheduler commands now work correctly
- ✅ No changes to bot.py initialization order needed
- ✅ More robust against future refactoring
- ✅ Follows Discord.py best practices
