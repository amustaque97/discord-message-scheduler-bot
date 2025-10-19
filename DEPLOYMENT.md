# Deployment Guide

This guide covers multiple deployment options for the Discord Message Scheduler Bot.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Appwrite Functions Deployment](#appwrite-functions-deployment)
- [Traditional Server Deployment](#traditional-server-deployment)
- [Environment Variables](#environment-variables)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Docker Deployment

### Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 1.29+)
- `.env` file configured with your credentials

### Quick Start

1. **Build and run with Docker Compose:**

   ```bash
   docker-compose up -d
   ```

2. **View logs:**

   ```bash
   docker-compose logs -f discord-bot
   ```

3. **Stop the bot:**
   ```bash
   docker-compose down
   ```

### Manual Docker Commands

If you prefer not to use Docker Compose:

```bash
# Build the image
docker build -t discord-scheduler:latest .

# Run the container
docker run -d \
  --name discord-scheduler \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  discord-scheduler:latest

# View logs
docker logs -f discord-scheduler

# Stop and remove
docker stop discord-scheduler
docker rm discord-scheduler
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:

- **Auto-restart** - Bot restarts automatically if it crashes
- **Resource limits** - CPU and memory limits for stability
- **Health checks** - Monitors bot health
- **Log rotation** - Prevents log files from growing too large
- **Volume mounting** - Persists logs outside the container

### Updating the Bot

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or with plain Docker
docker stop discord-scheduler
docker rm discord-scheduler
docker build -t discord-scheduler:latest .
docker run -d --name discord-scheduler --restart unless-stopped --env-file .env discord-scheduler:latest
```

---

## Appwrite Functions Deployment

**Note:** Discord bots require persistent connections, which are not ideal for serverless functions. However, you can deploy parts of the system as Appwrite Functions.

### Option 1: Deploy Bot as a Long-Running Container

While Appwrite Functions are typically serverless, you can deploy the bot as a long-running container in your Appwrite infrastructure.

1. **Build Docker image:**

   ```bash
   docker build -t discord-scheduler:latest .
   docker tag discord-scheduler:latest your-registry/discord-scheduler:latest
   docker push your-registry/discord-scheduler:latest
   ```

2. **Deploy to your infrastructure:**
   - Use your container orchestration platform (Kubernetes, Docker Swarm, etc.)
   - Ensure the container has access to Appwrite endpoints
   - Configure environment variables

### Option 2: Hybrid Deployment

Deploy the bot traditionally but use Appwrite Functions for specific tasks:

1. **Bot runs on a server** - Handles Discord connections and real-time events
2. **Appwrite Functions** - Handle scheduled tasks, webhooks, or API endpoints

Example Appwrite Function for cleanup tasks:

```javascript
// Appwrite Function: cleanup-old-messages
export default async ({ req, res, log, error }) => {
  const { Client, Databases, Query } = require('node-appwrite')

  const client = new Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT)
    .setProject(process.env.APPWRITE_PROJECT_ID)
    .setKey(process.env.APPWRITE_API_KEY)

  const databases = new Databases(client)

  try {
    // Delete sent messages older than 7 days
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

    const oldMessages = await databases.listDocuments(
      process.env.APPWRITE_DATABASE_ID,
      'scheduled_messages',
      [
        Query.equal('status', 'sent'),
        Query.lessThan('executed_at', sevenDaysAgo.toISOString()),
      ],
    )

    for (const msg of oldMessages.documents) {
      await databases.deleteDocument(
        process.env.APPWRITE_DATABASE_ID,
        'scheduled_messages',
        msg.$id,
      )
    }

    log(`Cleaned up ${oldMessages.documents.length} old messages`)
    return res.json({ success: true, deleted: oldMessages.documents.length })
  } catch (err) {
    error(err.message)
    return res.json({ success: false, error: err.message }, 500)
  }
}
```

---

## Traditional Server Deployment

### Option 1: Systemd Service (Linux)

1. **Create service file:**

   ```bash
   sudo nano /etc/systemd/system/discord-scheduler.service
   ```

2. **Add configuration:**

   ```ini
   [Unit]
   Description=Discord Message Scheduler Bot
   After=network.target

   [Service]
   Type=simple
   User=discord-bot
   WorkingDirectory=/opt/discord-scheduler
   Environment="PATH=/opt/discord-scheduler/venv/bin"
   EnvironmentFile=/opt/discord-scheduler/.env
   ExecStart=/opt/discord-scheduler/venv/bin/python /opt/discord-scheduler/bot.py
   Restart=always
   RestartSec=10

   # Security settings
   NoNewPrivileges=true
   PrivateTmp=true

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable discord-scheduler
   sudo systemctl start discord-scheduler
   sudo systemctl status discord-scheduler
   ```

4. **View logs:**
   ```bash
   sudo journalctl -u discord-scheduler -f
   ```

### Option 2: PM2 (Node.js Process Manager)

While PM2 is primarily for Node.js, it can manage Python processes too.

1. **Install PM2:**

   ```bash
   npm install -g pm2
   ```

2. **Create ecosystem file:**

   ```javascript
   // ecosystem.config.js
   module.exports = {
     apps: [
       {
         name: 'discord-scheduler',
         script: 'bot.py',
         interpreter: 'python3',
         cwd: '/path/to/discord-bot',
         instances: 1,
         autorestart: true,
         watch: false,
         max_memory_restart: '500M',
         env_file: '.env',
         error_file: './logs/error.log',
         out_file: './logs/out.log',
         log_file: './logs/combined.log',
         time: true,
       },
     ],
   }
   ```

3. **Start with PM2:**

   ```bash
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup  # Enable auto-start on boot
   ```

4. **Monitor:**
   ```bash
   pm2 status
   pm2 logs discord-scheduler
   pm2 monit
   ```

### Option 3: Screen/Tmux (Development/Quick Deploy)

For quick deployment or development:

```bash
# Using screen
screen -S discord-bot
cd /path/to/discord-bot
source venv/bin/activate
python bot.py

# Detach: Ctrl+A, then D
# Reattach: screen -r discord-bot

# Using tmux
tmux new -s discord-bot
cd /path/to/discord-bot
source venv/bin/activate
python bot.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t discord-bot
```

---

## Environment Variables

### Required Variables

```env
# Discord Bot Token (required)
DISCORD_TOKEN=your_discord_bot_token

# Appwrite Configuration (required)
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_api_key
```

### Optional Variables

```env
# Discord Guild ID for instant command sync (development)
DISCORD_GUILD_ID=your_test_guild_id

# Appwrite Database ID (default: discord_scheduler_db)
APPWRITE_DATABASE_ID=discord_scheduler_db

# Scheduler check interval in seconds (default: 60)
SCHEDULER_CHECK_INTERVAL=60

# Maximum retry attempts for failed messages (default: 3)
MAX_RETRY_ATTEMPTS=3

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
LOG_LEVEL=INFO
```

### Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use environment-specific files:**
   - `.env.development` - Local development
   - `.env.staging` - Staging environment
   - `.env.production` - Production environment

3. **Secure your environment files:**

   ```bash
   chmod 600 .env
   chown discord-bot:discord-bot .env
   ```

4. **Use secrets management** for production:
   - Docker Secrets
   - Kubernetes Secrets
   - HashiCorp Vault
   - AWS Secrets Manager / Azure Key Vault / GCP Secret Manager

---

## Monitoring and Maintenance

### Health Checks

The Docker image includes a health check that verifies the bot is running:

```bash
# Manual health check
docker exec discord-scheduler test -f /app/bot.log && echo "Healthy" || echo "Unhealthy"
```

### Log Management

#### View Logs

```bash
# Docker
docker-compose logs -f discord-bot

# Systemd
sudo journalctl -u discord-scheduler -f

# PM2
pm2 logs discord-scheduler

# Direct file
tail -f bot.log
```

#### Log Rotation

For systemd deployments, configure logrotate:

```bash
sudo nano /etc/logrotate.d/discord-scheduler
```

```
/opt/discord-scheduler/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    postrotate
        systemctl reload discord-scheduler
    endscript
}
```

### Resource Monitoring

Monitor CPU, memory, and disk usage:

```bash
# Docker stats
docker stats discord-scheduler

# PM2 monitoring
pm2 monit

# System resources
htop
top
```

### Database Maintenance

Run periodic cleanup of old data:

```bash
# Example: Delete logs older than 30 days
python -c "
from appwrite_client import AppwriteClient
from datetime import datetime, timedelta
import asyncio

async def cleanup():
    client = AppwriteClient()
    # Implement cleanup logic
    pass

asyncio.run(cleanup())
"
```

### Backup Strategy

1. **Appwrite Database Backups**
   - Regular exports of database collections
   - Store in S3/Cloud Storage
   - Test restore procedures

2. **Configuration Backups**
   - Version control for code
   - Secure storage for environment files
   - Document all custom configurations

### Updating Dependencies

```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip install safety
safety check

# Rebuild Docker image
docker-compose up -d --build
```

### Monitoring Checklist

- [ ] Bot is online and responding to commands
- [ ] Scheduler service is processing messages
- [ ] Database connectivity is stable
- [ ] Logs are being written and rotated
- [ ] No critical errors in recent logs
- [ ] Resource usage is within acceptable limits
- [ ] Scheduled messages are being sent on time

---

## Troubleshooting Deployment Issues

### Bot won't start

1. **Check logs first:**

   ```bash
   docker-compose logs discord-bot
   # or
   sudo journalctl -u discord-scheduler -n 50
   ```

2. **Common issues:**
   - Missing environment variables
   - Invalid Discord token
   - Incorrect Appwrite credentials
   - Port conflicts (if exposing ports)

### High memory usage

1. **Check for memory leaks:**

   ```bash
   docker stats discord-scheduler
   ```

2. **Adjust resource limits in docker-compose.yml**

3. **Review log levels** - DEBUG creates more logs

### Messages not being sent

1. **Verify scheduler is running:**
   - Check logs for "Scheduler service started"
2. **Check database connectivity:**
   - Test Appwrite connection manually
3. **Verify bot permissions in Discord**

---

## Production Checklist

Before deploying to production:

- [ ] Environment variables are properly secured
- [ ] Database is initialized and accessible
- [ ] Bot has required Discord permissions
- [ ] Auto-restart is configured
- [ ] Log rotation is set up
- [ ] Monitoring is in place
- [ ] Backup strategy is documented
- [ ] Security updates are automated
- [ ] Incident response plan is ready

---

## Support

For deployment assistance:

- Review logs for specific error messages
- Check Discord bot status in Developer Portal
- Verify Appwrite instance is accessible
- Consult the main [README.md](README.md) for configuration help

---

Made with ❤️ for easy deployment

