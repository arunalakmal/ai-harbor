# Frontend Connection Troubleshooting Guide

## Issue: Frontend shows "Failed to fetch" but backend works fine

If direct API calls work but the frontend can't connect, follow these steps:

### 🔍 **Step 1: Check Backend is Running**
```bash
# This should work (you mentioned it does)
curl http://localhost:8080/health
```

### 🔍 **Step 2: Check Frontend Configuration**
```bash
# Check what URL the frontend is trying to use
cat frontend/config.js

# Look for something like:
# window.ENV = { API_BASE_URL: 'http://localhost:8080' };
```

### 🔍 **Step 3: Check Browser Console**
1. Open frontend in browser: `http://localhost:3000`
2. Press `F12` to open Developer Tools
3. Go to **Console** tab
4. Look for these messages:
   ```
   Frontend running on: http://localhost:3000
   🏠 Local development mode detected
   ✅ Final API Base URL: http://localhost:8080
   Making API call to: http://localhost:8080/health
   ```
5. Look for **CORS errors** like:
   ```
   Access to fetch at 'http://localhost:8080/health' from origin 'http://localhost:3000' 
   has been blocked by CORS policy
   ```

### 🔍 **Step 4: Check Network Tab**
1. In Developer Tools, go to **Network** tab
2. Refresh the page
3. Look for failed requests to `localhost:8080`
4. Click on failed requests to see error details

### ✅ **Quick Fixes**

#### **Fix 1: Restart Backend with Proper CORS**
```bash
# Make sure these are NOT set when testing locally
unset SERVER_HOST
unset CORS_ORIGINS

# Restart backend (it will use localhost defaults)
python agent_api.py
```

#### **Fix 2: Configure Frontend Explicitly**
```bash
# Configure frontend to use localhost
cd frontend
./configure.sh local

# Start frontend
python -m http.server 3000
```

#### **Fix 3: Set CORS Explicitly**
```bash
# Allow your frontend origin
export CORS_ORIGINS="http://localhost:3000"
python agent_api.py
```

### 🔧 **Complete Reset Procedure**
```bash
# 1. Stop everything (Ctrl+C)

# 2. Clear environment variables
unset SERVER_HOST
unset CORS_ORIGINS
unset API_BASE_URL

# 3. Configure frontend for local
cd frontend
./configure.sh local

# 4. Start backend
python agent_api.py

# 5. Start frontend in new terminal
cd frontend
python -m http.server 3000

# 6. Test in browser: http://localhost:3000
```

### 🎯 **Expected Browser Console Output**
When working correctly, you should see:
```
Frontend running on: http://localhost:3000
🏠 Local development mode detected
✅ Final API Base URL: http://localhost:8080
📝 Config loaded - API URL: http://localhost:8080
Making API call to: http://localhost:8080/health
Response status: 200
API connection successful
```

### ❌ **Common Issues & Solutions**

| **Issue** | **Cause** | **Solution** |
|-----------|-----------|--------------|
| `Failed to fetch` | CORS blocking | Set `CORS_ORIGINS="http://localhost:3000"` |
| `ERR_CONNECTION_REFUSED` | Backend not running | Start `python agent_api.py` |
| `Wrong API URL in console` | Frontend misconfigured | Run `./frontend/configure.sh local` |
| `Mixed content error` | HTTP/HTTPS mismatch | Use same protocol (both HTTP locally) |

### 🔧 **Emergency Debug Script**
```bash
#!/bin/bash
echo "=== TROUBLESHOOTING FRONTEND CONNECTION ==="
echo ""

echo "1. Backend Health Check:"
curl -s http://localhost:8080/health || echo "❌ Backend not responding"
echo ""

echo "2. Frontend Config:"
cat frontend/config.js 2>/dev/null || echo "❌ No frontend config found"
echo ""

echo "3. Environment Variables:"
echo "   SERVER_HOST: ${SERVER_HOST:-'(not set)'}"
echo "   CORS_ORIGINS: ${CORS_ORIGINS:-'(not set)'}"
echo "   API_BASE_URL: ${API_BASE_URL:-'(not set)'}"
echo ""

echo "4. Running Processes:"
ps aux | grep -E "(python.*agent_api|python.*http.server)" | grep -v grep
echo ""

echo "5. Port Usage:"
lsof -i :8080 2>/dev/null || echo "   Port 8080: Not in use"
lsof -i :3000 2>/dev/null || echo "   Port 3000: Not in use"
```

### 🚀 **Quick Test**
```bash
# Test this exact sequence:
python agent_api.py &
API_BASE_URL=http://localhost:8080 ./frontend/start.sh
# Then open http://localhost:3000 in browser
```