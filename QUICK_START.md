# Quick Start Guide - Troubleshooting "Failed to fetch" Error

## The Error
If you're seeing "Failed to fetch" or "Failed to generate score", it means the frontend cannot connect to the backend API.

## Step-by-Step Fix

### 1. Verify Backend is Running

Open a terminal and check if the backend is running on port 8000:

```bash
# Check if port 8000 is in use
lsof -ti:8000
# OR on Windows:
netstat -ano | findstr :8000
```

If nothing is running, start the backend:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify environment variables are set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('CREDIT_PASSPORT_NFT_ADDRESS:', os.getenv('CREDIT_PASSPORT_NFT_ADDRESS', 'NOT SET'))"

# Start the backend
python -m uvicorn app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Test Backend Health Endpoint

Open your browser and go to: `http://localhost:8000/health`

You should see:
```json
{"status":"healthy","service":"AETHER-SCORE API","version":"1.0.0"}
```

If you get an error, check the backend terminal for error messages.

### 3. Verify Frontend Configuration

Check that `frontend/.env.local` has:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Or remove the file to use the default (which is now port 8000).

### 4. Restart Frontend Dev Server

If you made changes, restart the Next.js dev server:

```bash
cd frontend
# Stop the current server (Ctrl+C)
npm run dev
```

### 5. Check Browser Console

Open browser DevTools (F12) and check:
- **Console tab**: Look for any CORS errors or network errors
- **Network tab**: Check if the request to `http://localhost:8000/api/score` is being made and what the response is

## Common Issues

### Issue: "Environment validation failed"
**Solution**: The backend requires these environment variables in `backend/.env`:
- `CREDIT_PASSPORT_NFT_ADDRESS` (or `CREDIT_PASSPORT_ADDRESS`)
- `BACKEND_PRIVATE_KEY`
- `QIE_RPC_URL` (or `QIE_TESTNET_RPC_URL`)

### Issue: "CORS error"
**Solution**: Ensure `backend/.env` has:
```env
FRONTEND_URL=http://localhost:3000
```

### Issue: Backend starts but immediately crashes
**Solution**: Check the error message in the terminal. Common causes:
- Missing environment variables (startup validation will tell you which ones)
- Invalid private key format
- Invalid contract address format
- RPC URL unreachable

### Issue: "Cannot connect to backend"
**Solution**: 
1. Verify backend is actually running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Verify no other process is using port 8000

## Verification Checklist

- [ ] Backend is running on port 8000
- [ ] `http://localhost:8000/health` returns success
- [ ] `backend/.env` has all required variables
- [ ] `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000` (or uses default)
- [ ] Frontend dev server has been restarted after changes
- [ ] Browser console shows no CORS errors
- [ ] Network tab shows requests to `localhost:8000`

## Still Having Issues?

1. Check backend logs for detailed error messages
2. Check browser console for specific error details
3. Verify all environment variables are set correctly
4. Try accessing the API directly: `curl -X POST http://localhost:8000/api/score -H "Content-Type: application/json" -d '{"address":"0x0000000000000000000000000000000000000000"}'`

