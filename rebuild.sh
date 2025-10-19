#!/bin/bash
# Quick rebuild script for Discord Message Scheduler Bot

set -e

echo "🐳 Discord Message Scheduler - Docker Rebuild"
echo "=============================================="
echo ""

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

echo ""
echo "🔨 Rebuilding Docker image (this may take a minute)..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting bot container..."
docker-compose up -d

echo ""
echo "✅ Bot restarted with updated code!"
echo ""
echo "📋 Viewing logs (press Ctrl+C to exit)..."
echo "=============================================="
echo ""

# Show logs
docker-compose logs -f
