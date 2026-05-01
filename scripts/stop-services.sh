#!/bin/bash
# Stop AETHER-SCORE backend and frontend services

echo "ðŸ›‘ Stopping AETHER-SCORE Services"
echo "=============================="
echo ""

# Stop backend
if pkill -f 'uvicorn app:app' 2>/dev/null; then
    echo "âœ“ Backend stopped"
else
    echo "  Backend not running"
fi

# Stop frontend
if pkill -f 'next dev' 2>/dev/null; then
    echo "âœ“ Frontend stopped"
else
    echo "  Frontend not running"
fi

echo ""
echo "âœ… Services stopped"


