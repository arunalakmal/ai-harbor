#!/bin/bash

# Make scripts executable
chmod +x frontend/configure.sh
chmod +x frontend/start.sh

echo "✅ Scripts are now executable!"
echo ""
echo "🚀 Quick start examples:"
echo ""
echo "# Local development with environment variable:"
echo "API_BASE_URL=http://localhost:8080 ./frontend/start.sh"
echo ""
echo "# Production with environment variable:"
echo "API_BASE_URL=https://api.myapp.com ./frontend/start.sh"
echo ""
echo "# Auto-detection mode:"
echo "./frontend/start.sh"