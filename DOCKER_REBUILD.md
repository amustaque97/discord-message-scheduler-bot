# Docker Rebuild Instructions

## Problem

You're running the bot in Docker, and the container has the OLD code with the bug. The local files have been fixed, but Docker is still using the old cached version.

## Solution: Rebuild the Docker Image

### Step 1: Stop the Running Container

```bash
docker-compose down
```

### Step 2: Rebuild the Image (Force rebuild without cache)

```bash
docker-compose build --no-cache
```

**Or** if you want a quicker rebuild (uses cache for unchanged layers):

```bash
docker-compose build
```

### Step 3: Start the Container with New Code

```bash
docker-compose up -d
```

### Step 4: Check the Logs

```bash
docker-compose logs -f discord-bot
```

## Quick One-Liner (Recommended)

Stop, rebuild, and restart everything:

```bash
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

## Verify the Fix

After rebuilding, check the logs:

```bash
docker-compose logs -f
```

You should see:

- ✅ No more "NoneType" errors
- ✅ Bot connects successfully
- ✅ Commands work properly

Then test with:

```
/schedule_message
  channel: #your-channel
  message: Test after rebuild
  time: in 2 minutes
```

## Why This Happened

1. You edited the local files (✅ Fixed)
2. But Docker was still running the OLD image
3. Docker uses **image layers** - it doesn't automatically see your file changes
4. You must rebuild the image to include the new code

## Alternative: Development Mode with Volume Mount

For faster development (no rebuild needed), modify `docker-compose.yml` to mount the source code:

```yaml
services:
  discord-bot:
    # ... existing config ...
    volumes:
      - ./:/app # Mount current directory to /app in container
      - ./logs:/app/logs
```

Then changes to your Python files will be reflected immediately (just restart the container).

**Trade-off**: Slower startup, not recommended for production.

## Common Docker Commands

```bash
# Stop container
docker-compose down

# Rebuild without cache (clean build)
docker-compose build --no-cache

# Start in background
docker-compose up -d

# View logs (follow mode)
docker-compose logs -f

# Restart container
docker-compose restart

# View running containers
docker-compose ps

# Enter container shell
docker-compose exec discord-bot bash
```

## Quick Check if Code is Updated

After rebuilding, check if the new code is in the container:

```bash
docker-compose exec discord-bot grep -n "self.bot.appwrite_client" /app/commands/schedule_commands.py
```

You should see lines with `self.bot.appwrite_client` (not `self.appwrite_client`).
