# Restart Instructions

## Quick Restart

I've created a startup script for you. To restart everything:

```bash
# Stop any running processes
lsof -ti:3000,8000 | xargs kill -9 2>/dev/null

# Start everything
./start-dev.sh
```

## Manual Restart (Step by Step)

### 1. Stop Existing Processes

```bash
# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9

# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9
```

### 2. Start Backend

Open a terminal and run:

```bash
cd backend
source venv/bin/activate
python -m uvicorn app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal open!**

### 3. Start Frontend

Open a **new terminal** and run:

```bash
cd frontend
npm run dev
```

You should see:
```
  â–² Next.js 16.0.7
  - Local:        http://localhost:3000
```

### 4. Verify Everything Works

1. **Backend Health**: Open http://localhost:8000/health
   - Should show: `{"status":"healthy",...}`

2. **Frontend**: Open http://localhost:3000
   - Should load the AETHER-SCORE landing page

3. **Test Score Generation**: 
   - Connect wallet
   - Click "Generate Credit Passport"
   - Should work without "Failed to fetch" error

## Current Status

âœ… Frontend configuration: Correct (port 8000)
âœ… Backend environment variables: All set
âœ… API URL: http://localhost:8000

## If You Still See Errors

1. **Check backend terminal** for error messages
2. **Check browser console** (F12) for detailed errors
3. **Verify backend is running**: `curl http://localhost:8000/health`
4. **Check logs**: 
   - Backend: Look at the terminal where you started it
   - Frontend: Check browser console (F12)

## Troubleshooting

### "Failed to fetch" Error
- âœ… Backend must be running on port 8000
- âœ… Check `backend/.env` has all required variables
- âœ… Verify backend started without errors

### "Environment validation failed"
- Check `backend/.env` has:
  - `CREDIT_PASSPORT_NFT_ADDRESS` (or `CREDIT_PASSPORT_ADDRESS`)
  - `BACKEND_PRIVATE_KEY`
  - `QIE_RPC_URL` or `QIE_TESTNET_RPC_URL`

### CORS Errors
- Ensure `backend/.env` has: `FRONTEND_URL=http://localhost:3000`

