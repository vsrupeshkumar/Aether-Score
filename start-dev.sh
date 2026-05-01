#!/bin/bash

# AETHER-SCORE Development Startup Script
# This script starts both backend and frontend in development mode

set -e

echo "ðŸš€ Starting AETHER-SCORE Development Environment"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}âš ï¸  Backend is already running on port 8000${NC}"
    echo "   Kill it first with: lsof -ti:8000 | xargs kill -9"
    echo ""
else
    echo -e "${GREEN}âœ“${NC} Port 8000 is available for backend"
fi

# Check if frontend is already running
if lsof -ti:3000 > /dev/null 2>&1; then
    echo -e "${YELLOW}âš ï¸  Frontend is already running on port 3000${NC}"
    echo "   Kill it first with: lsof -ti:3000 | xargs kill -9"
    echo ""
else
    echo -e "${GREEN}âœ“${NC} Port 3000 is available for frontend"
fi

echo ""
echo "Starting services..."
echo ""

# Start backend in background
echo "ðŸ“¦ Starting Backend (port 8000)..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Check environment variables
if [ ! -f ".env" ]; then
    echo "âš ï¸  Warning: .env file not found. Copy from .env.example"
fi

# Start backend
python -m uvicorn app:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend started (PID: $BACKEND_PID)"
echo "   Logs: tail -f backend.log"

# Wait a bit for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}âœ“ Backend is healthy${NC}"
else
    echo -e "   ${YELLOW}âš ï¸  Backend may not be ready yet. Check backend.log${NC}"
fi

cd ..

# Start frontend
echo ""
echo "ðŸŽ¨ Starting Frontend (port 3000)..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

# Start frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend started (PID: $FRONTEND_PID)"
echo "   Logs: tail -f frontend.log"

cd ..

echo ""
echo -e "${GREEN}âœ… Development environment started!${NC}"
echo ""
echo "ðŸ“ Services:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "ðŸ“‹ Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "ðŸ›‘ To stop:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   OR: lsof -ti:8000,3000 | xargs kill -9"
echo ""

