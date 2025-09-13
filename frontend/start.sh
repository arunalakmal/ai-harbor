#!/bin/bash

# Frontend Startup Script with Environment Configuration
# This script configures and starts the frontend with backend URL from environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
PORT=${FRONTEND_PORT:-3000}
HOST=${FRONTEND_HOST:-0.0.0.0}

echo "🚀 Starting Frontend Server"
echo "================================"

# Configure backend URL from environment if provided
if [ ! -z "$API_BASE_URL" ]; then
    echo "🔧 Configuring backend URL from environment..."
    export API_BASE_URL="$API_BASE_URL"
    ./configure.sh
elif [ ! -z "$BACKEND_URL" ]; then
    echo "🔧 Configuring backend URL from BACKEND_URL..."
    export API_BASE_URL="$BACKEND_URL"
    ./configure.sh
else
    echo "ℹ️  No backend URL specified, using auto-detection"
    ./configure.sh auto
fi

echo ""
echo "🌐 Frontend Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
if [ ! -z "$API_BASE_URL" ]; then
    echo "   Backend: $API_BASE_URL"
else
    echo "   Backend: Auto-detection"
fi

echo ""
echo "🔗 Access URLs:"
echo "   Local: http://localhost:$PORT"
echo "   Network: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'YOUR-IP'):$PORT"

echo ""
echo "🏁 Starting Python HTTP server..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python3 -m http.server $PORT --bind $HOST