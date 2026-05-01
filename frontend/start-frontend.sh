#!/bin/bash
cd "$(dirname "$0")"
pkill -f "next dev" 2>/dev/null
sleep 1
npm run dev
