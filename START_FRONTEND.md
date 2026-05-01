# Frontend Startup Issue - Quick Fix

## Problem
The frontend keeps crashing when started in the background due to a Turbopack/Sentry configuration conflict.

## Solution

### Option 1: Start Frontend Manually (Recommended)
Open a terminal and run:
```bash
cd frontend
npm run dev
```

This will:
- Show you any errors in real-time
- Keep the process running
- Allow you to see what's happening

### Option 2: Use the Startup Script
```bash
cd frontend
./start-frontend.sh
```

## Current Status

✅ **Backend**: Running and healthy on http://localhost:8000
- Health check: http://localhost:8000/health
- API working correctly

❌ **Frontend**: Needs to be started manually
- The background process keeps crashing
- Manual start will show the actual error

## Why This Happens

Next.js 16 defaults to Turbopack, but Sentry doesn't fully support it yet. The `--webpack` flag should work, but when running in background, the process may exit before fully starting.

## Once Frontend Starts

1. Open http://localhost:3000
2. Connect wallet
3. Generate score - should work perfectly!

The backend is ready and waiting. The "Failed to fetch" error will be resolved once the frontend is running.
