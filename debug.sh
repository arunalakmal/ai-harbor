#!/bin/bash

echo "🔍 FRONTEND CONNECTION TROUBLESHOOTING"
echo "======================================"
echo ""

echo "📡 1. Testing Backend Connection:"
if curl -s http://localhost:8080/health > /dev/null; then
    echo "   ✅ Backend is responding on http://localhost:8080"
    curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo "   📋 Response: $(curl -s http://localhost:8080/health)"
else
    echo "   ❌ Backend is NOT responding on http://localhost:8080"
    echo "   💡 Start backend with: python agent_api.py"
fi
echo ""

echo "⚙️  2. Frontend Configuration:"
if [ -f "frontend/config.js" ]; then
    echo "   📝 Frontend config exists:"
    cat frontend/config.js | grep -A2 -B2 "API_BASE_URL"
else
    echo "   ❌ No frontend config found at frontend/config.js"
    echo "   💡 Run: cd frontend && ./configure.sh local"
fi
echo ""

echo "🌍 3. Environment Variables:"
echo "   SERVER_HOST: ${SERVER_HOST:-'(not set - will use localhost)'}"
echo "   CORS_ORIGINS: ${CORS_ORIGINS:-'(not set - will use defaults)'}"
echo "   API_BASE_URL: ${API_BASE_URL:-'(not set - frontend will auto-detect)'}"
echo ""

echo "🔧 4. Running Processes:"
BACKEND_PROC=$(ps aux | grep -E "python.*agent_api" | grep -v grep)
FRONTEND_PROC=$(ps aux | grep -E "python.*http.server.*3000" | grep -v grep)

if [ ! -z "$BACKEND_PROC" ]; then
    echo "   ✅ Backend is running: $(echo $BACKEND_PROC | awk '{print $2}')"
else
    echo "   ❌ Backend process not found"
fi

if [ ! -z "$FRONTEND_PROC" ]; then
    echo "   ✅ Frontend is running: $(echo $FRONTEND_PROC | awk '{print $2}')"
else
    echo "   ❌ Frontend process not found"
fi
echo ""

echo "🔌 5. Port Status:"
if lsof -i :8080 > /dev/null 2>&1; then
    echo "   ✅ Port 8080 is in use (backend)"
else
    echo "   ❌ Port 8080 is free (backend not listening)"
fi

if lsof -i :3000 > /dev/null 2>&1; then
    echo "   ✅ Port 3000 is in use (frontend)"
else
    echo "   ❌ Port 3000 is free (frontend not running)"
fi
echo ""

echo "🎯 6. Quick Fix Commands:"
echo "   # Clear environment and restart everything:"
echo "   unset SERVER_HOST CORS_ORIGINS API_BASE_URL"
echo "   python agent_api.py &"
echo "   cd frontend && ./configure.sh local && python -m http.server 3000"
echo ""
echo "   # Or use the startup script:"
echo "   API_BASE_URL=http://localhost:8080 ./frontend/start.sh"
echo ""

echo "🌐 7. Browser Test:"
echo "   Open: http://localhost:3000"
echo "   Press F12 → Console tab"
echo "   Look for: 'Final API Base URL: http://localhost:8080'"
echo "   Look for CORS errors or connection failures"