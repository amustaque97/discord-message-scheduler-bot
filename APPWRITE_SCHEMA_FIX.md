# Appwrite Schema Fix

## Issue

When running the bot, you encountered:

```
AppwriteException: Invalid query: Attribute not found in schema: status
```

## Root Cause

The Appwrite database collections existed but were missing critical attributes (`status`, `retry_count`, `timezone`, `max_scheduled_messages`, `notification_enabled`) because:

1. The original setup script skipped attribute creation if collections already existed
2. Appwrite SDK 13.x changed the rules: **required attributes cannot have default values**

## Solution Applied

### 1. Fixed Schema Definition (setup_appwrite.py)

Changed attributes from `required: True` to `required: False` for fields with default values:

**scheduled_messages collection:**

- `status`: `required: True` → `required: False` (default: "pending")
- `retry_count`: `required: True` → `required: False` (default: 0)

**user_preferences collection:**

- `timezone`: `required: True` → `required: False` (default: "UTC")
- `max_scheduled_messages`: `required: True` → `required: False` (default: 10)
- `notification_enabled`: `required: True` → `required: False` (default: True)

### 2. Improved Setup Script

Added `get_collection_attributes()` function to:

- Check existing attributes before attempting to create them
- Only create missing attributes
- Handle index creation errors gracefully (skip if already exists)

## Results

After running the updated setup script:

```
✅ Created attribute 'status'
✅ Created attribute 'retry_count'
✅ Created index 'idx_status'
✅ Created index 'idx_status_scheduled_time'
✅ Created attribute 'timezone'
✅ Created attribute 'max_scheduled_messages'
✅ Created attribute 'notification_enabled'
```

## Verification

Bot now starts successfully:

```
✅ Appwrite client initialized
✅ Scheduler service initialized
✅ Commands synced to guild
✅ Bot connected to Gateway
```

## Important Notes

### Appwrite SDK 13.x Schema Rules:

1. **Required attributes CANNOT have default values**
2. **Optional attributes CAN have default values**
3. This is different from SDK 5.x behavior

### Application Logic Impact:

Since these attributes are now optional with defaults, the application code must ensure:

- `status` is always set when creating documents (appwrite_client.py handles this ✅)
- `retry_count` defaults to 0 via Appwrite (handled by database)
- User preferences have sensible defaults (handled by database)

## Files Modified

1. `setup_appwrite.py` - Fixed schema definitions and improved attribute checking
2. Database schema now matches SDK 13.x requirements

## No Code Changes Required

The application code in `appwrite_client.py` already sets these values explicitly when creating documents, so no changes were needed in the bot logic.
