#!/usr/bin/env python3
"""
Azure OpenAI Agent using direct HTTP requests (no library dependency issues)
"""

import os
import sys
import time
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import urllib.error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
AGENT_ID = os.environ.get("AGENT_ID", "unknown")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
DEPLOYMENT_NAME = os.environ.get("AZURE_DEPLOYMENT_NAME", "pstestopenaidply-axk22t6757r7c")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "general")

# Azure OpenAI configuration
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip('/')
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Standard OpenAI fallback
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# System prompts
SYSTEM_PROMPTS = {
    "general": "You are a helpful AI assistant powered by Azure OpenAI. Provide clear, accurate, and helpful responses.",
    "coder": "You are an expert software developer using Azure OpenAI. Help with coding questions, debugging, and best practices. Always provide working code examples.",
    "analyzer": "You are a data analyst powered by Azure OpenAI. Help analyze information, create summaries, and extract actionable insights.",
    "creative": "You are a creative writer using Azure OpenAI. Help with storytelling, creative writing, and imaginative content creation."
}

# Check for custom system prompt first, then fall back to predefined prompts
CUSTOM_SYSTEM_PROMPT = os.environ.get("CUSTOM_SYSTEM_PROMPT", "")
if CUSTOM_SYSTEM_PROMPT:
    SYSTEM_PROMPT = CUSTOM_SYSTEM_PROMPT
else:
    SYSTEM_PROMPT = SYSTEM_PROMPTS.get(AGENT_TYPE, SYSTEM_PROMPTS["general"])

class DirectHTTPAzureAgent:
    """Direct HTTP client for Azure OpenAI to bypass library issues"""
    
    def __init__(self):
        self.azure_available = bool(AZURE_ENDPOINT and AZURE_API_KEY)
        self.openai_available = bool(OPENAI_API_KEY)
        
        if self.azure_available:
            # Construct Azure OpenAI URL
            self.azure_url = f"{AZURE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_API_VERSION}"
            logger.info(f"✅ Azure OpenAI configured: {AZURE_ENDPOINT}")
            logger.info(f"✅ Deployment: {DEPLOYMENT_NAME}")
        
        if self.openai_available:
            self.openai_url = "https://api.openai.com/v1/chat/completions"
            logger.info("✅ OpenAI fallback configured")
        
        if not self.azure_available and not self.openai_available:
            logger.warning("⚠️ No AI backends configured - will run in echo mode")
    
    def call_azure_openai(self, messages, user_id="anonymous"):
        """Call Azure OpenAI using direct HTTP request"""
        try:
            # Prepare request data
            data = {
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7,
                "user": user_id
            }
            
            # Convert to JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Create request
            request = urllib.request.Request(
                self.azure_url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'api-key': AZURE_API_KEY
                },
                method='POST'
            )
            
            logger.info(f"🔄 Calling Azure OpenAI: {self.azure_url}")
            
            # Make request
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode('utf-8'))
                    logger.info("✅ Azure OpenAI response received")
                    return response_data, "azure_openai"
                else:
                    error_msg = f"Azure OpenAI HTTP {response.status}: {response.read().decode('utf-8')}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except urllib.error.HTTPError as e:
            error_msg = f"Azure OpenAI HTTP Error {e.code}: {e.read().decode('utf-8') if e.fp else str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except urllib.error.URLError as e:
            error_msg = f"Azure OpenAI Network Error: {e.reason}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Azure OpenAI Error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def call_openai(self, messages, user_id="anonymous"):
        """Call standard OpenAI using direct HTTP request"""
        try:
            # Prepare request data
            data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7,
                "user": user_id
            }
            
            # Convert to JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Create request
            request = urllib.request.Request(
                self.openai_url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                },
                method='POST'
            )
            
            logger.info("🔄 Calling standard OpenAI")
            
            # Make request
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode('utf-8'))
                    logger.info("✅ OpenAI response received")
                    return response_data, "openai"
                else:
                    error_msg = f"OpenAI HTTP {response.status}: {response.read().decode('utf-8')}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except Exception as e:
            error_msg = f"OpenAI Error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def chat(self, message, user_id="anonymous"):
        """Main chat method with fallback logic"""
        # Prepare messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
        
        # Try Azure OpenAI first
        if self.azure_available:
            try:
                response_data, backend = self.call_azure_openai(messages, user_id)
                return response_data, backend
            except Exception as azure_error:
                logger.error(f"Azure OpenAI failed: {azure_error}")
                
                # Try standard OpenAI fallback
                if self.openai_available:
                    logger.info("🔄 Falling back to standard OpenAI...")
                    try:
                        response_data, backend = self.call_openai(messages, user_id)
                        return response_data, f"{backend}_fallback"
                    except Exception as openai_error:
                        logger.error(f"OpenAI fallback also failed: {openai_error}")
                        raise azure_error  # Raise original Azure error
                else:
                    raise azure_error
        
        # Try standard OpenAI if Azure not available
        elif self.openai_available:
            response_data, backend = self.call_openai(messages, user_id)
            return response_data, backend
        
        else:
            raise Exception("No AI backends configured")

# Initialize the direct HTTP client
ai_client = DirectHTTPAzureAgent()

class DirectHTTPAgentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        if self.path == '/health':
            self._send_response(200, {
                "status": "healthy",
                "agent_id": AGENT_ID,
                "agent_type": AGENT_TYPE,
                "model": MODEL_NAME,
                "deployment": DEPLOYMENT_NAME,
                "ai_backend": "azure_openai_direct" if ai_client.azure_available else ("openai_direct" if ai_client.openai_available else "echo"),
                "azure_configured": ai_client.azure_available,
                "openai_fallback": ai_client.openai_available,
                "azure_endpoint": AZURE_ENDPOINT if ai_client.azure_available else None,
                "direct_http": True,
                "library_bypass": True,
                "timestamp": time.time()
            })
        elif self.path == '/status':
            self._send_response(200, {
                "agent_id": AGENT_ID,
                "type": AGENT_TYPE,
                "model": MODEL_NAME,
                "deployment": DEPLOYMENT_NAME,
                "status": "running",
                "ai_backend": "azure_openai_direct" if ai_client.azure_available else ("openai_direct" if ai_client.openai_available else "echo"),
                "capabilities": ["chat", "text-generation"] if (ai_client.azure_available or ai_client.openai_available) else ["echo"],
                "direct_http": True,
                "system_prompt_preview": SYSTEM_PROMPT[:100] + "..." if len(SYSTEM_PROMPT) > 100 else SYSTEM_PROMPT
            })
        else:
            self._send_response(404, {"error": "Not found"})
    
    def do_POST(self):
        if self.path == '/chat':
            if ai_client.azure_available or ai_client.openai_available:
                self._handle_ai_chat()
            else:
                self._handle_echo_chat()
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _handle_echo_chat(self):
        """Fallback echo chat"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            
            self._send_response(200, {
                "response": f"Direct HTTP agent {AGENT_ID[:8]} (echo mode): {message}",
                "agent_id": AGENT_ID,
                "ai_backend": "echo",
                "timestamp": time.time(),
                "note": "No AI backends configured"
            })
            
        except Exception as e:
            self._send_response(500, {"error": str(e)})
    
    def _handle_ai_chat(self):
        """Handle AI chat using direct HTTP"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '').strip()
            user_id = data.get('user_id', 'anonymous')
            
            if not message:
                self._send_response(400, {"error": "No message provided"})
                return
            
            # Call AI using direct HTTP
            try:
                response_data, backend_used = ai_client.chat(message, user_id)
                
                # Extract response text and usage info
                ai_response = response_data['choices'][0]['message']['content']
                usage_info = response_data.get('usage', {})
                
                response_payload = {
                    "response": ai_response,
                    "agent_id": AGENT_ID,
                    "model": MODEL_NAME,
                    "deployment": DEPLOYMENT_NAME if backend_used.startswith("azure") else None,
                    "ai_backend": backend_used,
                    "azure_endpoint": AZURE_ENDPOINT if backend_used.startswith("azure") else None,
                    "direct_http": True,
                    "timestamp": time.time(),
                    "user_id": user_id,
                    "usage": {
                        "prompt_tokens": usage_info.get('prompt_tokens', 0),
                        "completion_tokens": usage_info.get('completion_tokens', 0),
                        "total_tokens": usage_info.get('total_tokens', 0)
                    }
                }
                
                self._send_response(200, response_payload)
                
            except Exception as ai_error:
                logger.error(f"AI processing error: {ai_error}")
                self._send_response(500, {
                    "error": f"AI processing failed: {str(ai_error)}",
                    "agent_id": AGENT_ID,
                    "direct_http": True,
                    "fallback_response": f"Error from direct HTTP agent {AGENT_ID[:8]}: {str(ai_error)}"
                })
                
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON in request"})
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            self._send_response(500, {"error": f"Request handling failed: {str(e)}"})
    
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Agent-ID', AGENT_ID)
        self.send_header('X-Direct-HTTP', 'true')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

def start_server():
    try:
        server = HTTPServer(('0.0.0.0', 8080), DirectHTTPAgentHandler)
        
        logger.info(f"🚀 Starting Direct HTTP Azure OpenAI Agent {AGENT_ID[:8]} on port 8080")
        
        if ai_client.azure_available:
            logger.info(f"✅ Azure OpenAI Direct HTTP: {AZURE_ENDPOINT}")
            logger.info(f"✅ Deployment: {DEPLOYMENT_NAME}")
            logger.info(f"✅ Model: {MODEL_NAME}")
        elif ai_client.openai_available:
            logger.info("✅ Standard OpenAI Direct HTTP configured")
        else:
            logger.warning("⚠️ No AI backends - running in echo mode")
        
        logger.info(f"🤖 Agent Type: {AGENT_TYPE}")
        logger.info(f"💭 System Prompt: {SYSTEM_PROMPT[:50]}...")
        logger.info("🔄 Using direct HTTP requests (no OpenAI library dependency)")
        
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_server()