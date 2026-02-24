#!/bin/bash

# Stop any existing Next.js dev servers
echo "🛑 Stopping existing servers..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
pkill -f "next" 2>/dev/null || true
sleep 1

# Increase file descriptor limit
ulimit -n 65536 2>/dev/null || ulimit -n 10240

# Clear Next.js cache
echo "🧹 Clearing cache..."
rm -rf .next

# Build project
echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
  echo "❌ Build failed!"
  exit 1
fi

# Start production server
echo "🚀 Starting production server on port 3000..."
PORT=3000 npm start
