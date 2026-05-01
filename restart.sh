#!/bin/bash

# Simple restart script for AETHER-SCORE

echo "ðŸ›‘ Stopping existing services..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2

echo ""
echo "ðŸ“¦ Installing/updating dependencies..."

# Backend dependencies
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
cd ..

# Frontend dependencies
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi
cd ..

echo ""
echo "âœ… Dependencies ready"
echo ""
echo "ðŸš€ To start the application, open TWO terminals:"
echo ""
echo "TERMINAL 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app:app --reload --port 8000"
echo ""
echo "TERMINAL 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""

