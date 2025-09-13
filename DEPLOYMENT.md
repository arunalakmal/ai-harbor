# Production Deployment Guide

This guide shows how to deploy the Containerized Agents API to production environments.

## Frontend Backend Configuration

The frontend can be configured to connect to any backend URL using environment variables or configuration scripts.

### **🌍 Environment Variable Method (Recommended)**

#### **Local Development**
```bash
# Set backend URL and start frontend
export API_BASE_URL=http://localhost:8080
cd frontend && ./start.sh

# Or inline:
API_BASE_URL=http://localhost:8080 ./frontend/start.sh
```

#### **Production**
```bash
# Set backend URL and start frontend
export API_BASE_URL=https://api.myapp.com
cd frontend && ./start.sh

# Or with custom port:
API_BASE_URL=https://api.myapp.com FRONTEND_PORT=80 ./frontend/start.sh
```

#### **Local Network**
```bash
# Set backend URL for local network testing
export API_BASE_URL=http://192.168.1.100:8080
cd frontend && ./start.sh
```

#### **Custom Backend**
```bash
# Connect to any backend
export API_BASE_URL=https://my-custom-api.com:9000
cd frontend && ./start.sh
```

### **🔧 Configuration Script Method**

```bash
cd frontend

# Local development
./configure.sh local

# Local network (specify IP)
./configure.sh network 192.168.1.100

# Production (specify domain)
./configure.sh production myapp.com

# Custom URL
./configure.sh custom https://api.mycompany.com:9000

# Auto-detection (default)
./configure.sh auto
```

### **📋 Environment Variables**

| **Variable** | **Description** | **Default** | **Example** |
|--------------|-----------------|-------------|-------------|
| `API_BASE_URL` | Backend API URL | Auto-detect | `https://api.myapp.com` |
| `BACKEND_URL` | Alternative name for API_BASE_URL | - | `http://localhost:8080` |
| `FRONTEND_PORT` | Frontend server port | `3000` | `80` |
| `FRONTEND_HOST` | Frontend bind address | `0.0.0.0` | `localhost` |

### **🚀 Quick Start Examples**

#### **Complete Local Setup**
```bash
# Terminal 1: Start backend
python agent_api.py

# Terminal 2: Start frontend with explicit backend URL
API_BASE_URL=http://localhost:8080 ./frontend/start.sh
```

#### **Production Setup**
```bash
# Set all environment variables
export API_BASE_URL=https://api.mycompany.com
export FRONTEND_PORT=80
export FRONTEND_HOST=0.0.0.0

# Start frontend
cd frontend && ./start.sh
```

#### **Docker Environment**
```bash
# Run frontend container with backend URL
docker run -e API_BASE_URL=https://api.myapp.com -p 3000:3000 my-frontend

# Or with docker-compose
API_BASE_URL=https://api.myapp.com docker-compose up
```

#### **One-liner Deployment**
```bash
# Start both backend and frontend with one command
python agent_api.py & API_BASE_URL=http://localhost:8080 ./frontend/start.sh
```

### **Configuration Examples**

| **Environment** | **Command** | **Frontend Config** | **Result** |
|----------------|-------------|-------------------|------------|
| **Local Dev** | `./configure.sh local` | `API_BASE_URL: 'http://localhost:8080'` | Frontend → `localhost:8080` |
| **Local Network** | `./configure.sh network 192.168.1.100` | `API_BASE_URL: 'http://192.168.1.100:8080'` | Frontend → `192.168.1.100:8080` |
| **Production** | `./configure.sh production myapp.com` | `API_BASE_URL: 'https://myapp.com:8080'` | Frontend → `myapp.com:8080` |
| **Custom** | `./configure.sh custom https://api.example.com` | `API_BASE_URL: 'https://api.example.com'` | Frontend → `api.example.com` |
| **Auto-detect** | `./configure.sh auto` | `API_BASE_URL: undefined` | Frontend → Auto-detection |

## Local Development

### **Option 1: Explicit Configuration**
```bash
# 1. Configure frontend
cd frontend
./configure.sh local

# 2. Start backend
python agent_api.py

# 3. Start frontend
python -m http.server 3000
```

### **Option 2: Auto-detection (Default)**
```bash
# No configuration needed - uses auto-detection
python agent_api.py
cd frontend && python -m http.server 3000
```

## Production Deployment

### **1. Environment Variables**

Set these environment variables for production:

```bash
# Azure OpenAI Configuration (Required)
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_DEPLOYMENT_NAME="your-deployment-name"

# Production Configuration
export SERVER_HOST="your-domain.com"  # or public IP
export CORS_ORIGINS="https://your-domain.com,https://www.your-domain.com"
```

### **2. Deployment Scenarios**

#### **Same Server Deployment**
```bash
# Configure frontend for production
cd frontend
./configure.sh production myapp.com

# Start backend
export SERVER_HOST="myapp.com"
export CORS_ORIGINS="https://myapp.com"
python agent_api.py &

# Start frontend  
python -m http.server 80 &
```

#### **Separate API Server**
```bash
# Backend on api.myapp.com
cd frontend
./configure.sh custom https://api.myapp.com

# Backend server
export SERVER_HOST="api.myapp.com"
export CORS_ORIGINS="https://myapp.com"
python agent_api.py

# Frontend server (different machine)
python -m http.server 80
```

### **3. Cloud Platform Examples**

#### **AWS EC2**
```bash
# Configure for EC2 public IP
cd frontend
./configure.sh network your-ec2-public-ip

# Set environment variables
export SERVER_HOST="your-ec2-public-ip"
export CORS_ORIGINS="http://your-ec2-public-ip:3000"

# Start services
python agent_api.py &
cd frontend && python -m http.server 3000 &
```

#### **DigitalOcean with Custom Domain**
```bash
# Configure for custom domain
cd frontend
./configure.sh production myapp.digitaloceanspaces.com

# Backend configuration
export SERVER_HOST="myapp.digitaloceanspaces.com"
export CORS_ORIGINS="https://myapp.digitaloceanspaces.com"
python agent_api.py &
cd frontend && python -m http.server 80 &
```

### **4. Docker Deployment**

#### **Docker Compose**
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SERVER_HOST=localhost
      - CORS_ORIGINS=http://localhost:3000
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    # Frontend config is set during build
```

#### **Frontend Dockerfile**
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html

# Configure for production during build
ARG API_BASE_URL=http://localhost:8080
RUN echo "window.ENV = { API_BASE_URL: '$API_BASE_URL' };" > /usr/share/nginx/html/config.js
```

Build with custom API URL:
```bash
docker build --build-arg API_BASE_URL=https://api.myapp.com -t my-frontend .
```

### **5. Configuration Priority**

The frontend uses this priority order:

1. **`window.ENV.API_BASE_URL`** (from config.js) - **Highest Priority**
2. **`process.env.API_BASE_URL`** (build-time environment)
3. **Auto-detection** (based on current hostname) - **Lowest Priority**

### **6. Testing Configuration**

Check your configuration in browser console:

```javascript
// Open browser console (F12) and check:
console.log('API Base URL:', API_BASE_URL);
console.log('Frontend Config:', window.ENV);
```

### **7. Configuration Script Usage**

```bash
# Make script executable (first time)
chmod +x frontend/configure.sh

# Quick configuration commands
cd frontend

# Development
./configure.sh local

# Test on local network
./configure.sh network $(hostname -I | awk '{print $1}')

# Production
./configure.sh production $(echo $SERVER_HOST)

# Check current configuration
cat config.js
```

The frontend now **explicitly knows where to find the backend** through configuration! 🎯