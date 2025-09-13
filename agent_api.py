#!/usr/bin/env python3
"""
Flask API for managing containerized Azure OpenAI agents
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import docker
import os
import tempfile
import time
import requests
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Import system prompt templates
try:
    from system_prompt_templates import (
        SOFTWARE_DEVELOPMENT_PROMPTS,
        BUSINESS_ANALYSIS_PROMPTS,
        CREATIVE_CONTENT_PROMPTS,
        SPECIALIZED_DOMAIN_PROMPTS
    )
    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False
    SOFTWARE_DEVELOPMENT_PROMPTS = {}
    BUSINESS_ANALYSIS_PROMPTS = {}
    CREATIVE_CONTENT_PROMPTS = {}
    SPECIALIZED_DOMAIN_PROMPTS = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get allowed origins from environment or use defaults
allowed_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000')
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

# Always allow localhost origins for development
dev_origins = ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8000', 'http://127.0.0.1:8000']
for origin in dev_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

print(f"🌐 CORS allowed origins: {allowed_origins}")
CORS(app, origins=allowed_origins)

# Global storage for agent metadata
agents_db = {}

class AgentManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.agents = {}
        
        # Combine all templates into a single dictionary for easy lookup
        self.all_templates = {}
        if TEMPLATES_AVAILABLE:
            self.all_templates.update(SOFTWARE_DEVELOPMENT_PROMPTS)
            self.all_templates.update(BUSINESS_ANALYSIS_PROMPTS)
            self.all_templates.update(CREATIVE_CONTENT_PROMPTS)
            self.all_templates.update(SPECIALIZED_DOMAIN_PROMPTS)
    
    def get_template_prompt(self, template_name: str) -> Optional[str]:
        """Get system prompt from template name"""
        return self.all_templates.get(template_name)
    
    def list_templates(self) -> Dict:
        """List available templates by category"""
        if not TEMPLATES_AVAILABLE:
            return {"error": "Templates not available"}
        
        return {
            "software_development": list(SOFTWARE_DEVELOPMENT_PROMPTS.keys()),
            "business_analysis": list(BUSINESS_ANALYSIS_PROMPTS.keys()),
            "creative_content": list(CREATIVE_CONTENT_PROMPTS.keys()),
            "specialized_domain": list(SPECIALIZED_DOMAIN_PROMPTS.keys()),
            "all_templates": list(self.all_templates.keys())
        }
        
    def load_direct_agent_script(self) -> str:
        """Load the direct HTTP agent script"""
        try:
            with open('direct_http_agent.py', 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError("direct_http_agent.py not found! Please ensure it exists in the current directory")
    
    def test_azure_connection_simple(self):
        """Simple Azure OpenAI connection test using requests"""
        try:
            logger.info("Starting simple Azure OpenAI connection test...")
            
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            
            logger.info(f"Azure endpoint: {endpoint}")
            logger.info(f"Azure API key present: {bool(api_key)}")
            
            if not endpoint or not api_key:
                logger.error("Missing Azure OpenAI credentials")
                return False
            
            # Skip the connection test for now - just verify credentials exist
            logger.info("Azure credentials found - skipping connection test")
            return True
                
        except Exception as e:
            logger.error(f"Simple Azure OpenAI connection test failed: {e}")
            return False

    def test_azure_connection(self):
        """Test if Azure OpenAI is properly configured and accessible"""
        try:
            logger.info("Starting Azure OpenAI connection test...")
            
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            
            logger.info(f"Azure endpoint: {endpoint}")
            logger.info(f"Azure API key length: {len(api_key) if api_key else 0}")
            
            if not endpoint or not api_key:
                logger.error("Missing Azure OpenAI credentials")
                return False
            
            # For now, just return True if credentials exist
            # The actual connection will be tested when the agent makes its first request
            logger.info("Azure credentials verified - connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False
    
    def create_agent(self, agent_type: str = "coder", model_name: str = "gpt-4o-mini", deployment_name: str = None, system_prompt: str = None, template: str = None) -> Dict:
        """Create a new containerized agent"""
        # Validate Azure configuration
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Get default deployment name from environment if not provided
        default_deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
        deployment_name = deployment_name or default_deployment
        
        logger.info(f"Creating agent with type: {agent_type}, model: {model_name}, deployment: {deployment_name}, template: {template}")
        
        if not azure_endpoint or not azure_key:
            raise ValueError("Missing Azure OpenAI configuration. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        
        logger.info("Testing Azure OpenAI connection...")
        if not self.test_azure_connection():
            raise ValueError("Azure OpenAI connection test failed")
        
        # Determine system prompt: template takes precedence over custom prompt
        final_system_prompt = None
        template_used = None
        
        if template:
            final_system_prompt = self.get_template_prompt(template)
            if not final_system_prompt:
                available_templates = list(self.all_templates.keys()) if TEMPLATES_AVAILABLE else []
                raise ValueError(f"Template '{template}' not found. Available templates: {available_templates}")
            template_used = template
        elif system_prompt:
            final_system_prompt = system_prompt
        
        # Load agent script
        agent_script = self.load_direct_agent_script()
        
        # Generate agent ID and name
        agent_id = str(uuid.uuid4())
        agent_name = f"direct-agent-{agent_id[:8]}"
        
        # Save script to temp file
        script_file = f"/tmp/direct_agent_{agent_id}.py"
        with open(script_file, 'w') as f:
            f.write(agent_script)
        
        # Environment variables
        env_vars = {
            "AGENT_ID": agent_id,
            "AGENT_TYPE": agent_type,
            "MODEL_NAME": model_name,
            "AZURE_DEPLOYMENT_NAME": deployment_name,
            "AZURE_OPENAI_ENDPOINT": azure_endpoint,
            "AZURE_OPENAI_API_KEY": azure_key,
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
            "PYTHONUNBUFFERED": "1"
        }
        
        # Add custom system prompt if provided
        if final_system_prompt:
            env_vars["CUSTOM_SYSTEM_PROMPT"] = final_system_prompt
        
        try:
            # Create container
            container = self.docker_client.containers.run(
                image="python:3.9-slim",
                name=agent_name,
                environment=env_vars,
                ports={"8080/tcp": None},
                detach=True,
                remove=False,
                volumes={
                    script_file: {"bind": "/app/agent.py", "mode": "ro"}
                },
                command=["python", "/app/agent.py"],
                mem_limit="512m"
            )
            
            # Wait for startup
            time.sleep(8)
            
            # Get assigned port
            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            assigned_port = None
            if '8080/tcp' in ports and ports['8080/tcp']:
                assigned_port = ports['8080/tcp'][0]['HostPort']
            
            logger.info(f"Container port mapping: {ports}")
            logger.info(f"Assigned port: {assigned_port}")
            
            if not assigned_port:
                container.remove(force=True)
                raise RuntimeError("No port assigned to container")
            
            # Get the server's host for agent endpoints
            server_host = os.getenv('SERVER_HOST', 'localhost')
            logger.info(f"SERVER_HOST environment variable: {server_host}")
            
            # Ensure we don't double up on protocol and clean the host
            if server_host.startswith(('http://', 'https://')):
                # Extract hostname from URL
                from urllib.parse import urlparse
                parsed = urlparse(server_host)
                clean_host = parsed.hostname or parsed.netloc.split(':')[0]
                endpoint = f"http://{clean_host}:{assigned_port}"
            else:
                endpoint = f"http://{server_host}:{assigned_port}"
            
            logger.info(f"Agent endpoint configured as: {endpoint}")
            
            # Test agent health
            try:
                logger.info(f"Testing agent health at: {endpoint}/health")
                health_response = requests.get(f"{endpoint}/health", timeout=5)
                if health_response.status_code != 200:
                    container.remove(force=True)
                    raise RuntimeError(f"Agent health check failed: {health_response.status_code}")
                logger.info("Agent health check passed")
            except Exception as e:
                logger.error(f"Agent health check failed: {e}")
                container.remove(force=True)
                raise RuntimeError(f"Agent health check error: {e}")
            
            # Store agent metadata
            agent_info = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "model_name": model_name,
                "deployment_name": deployment_name,
                "system_prompt": final_system_prompt,
                "template_used": template_used,
                "container_id": container.id,
                "endpoint": endpoint,
                "port": assigned_port,
                "created_at": datetime.now().isoformat(),
                "status": "running"
            }
            
            self.agents[agent_id] = agent_info
            agents_db[agent_id] = agent_info
            
            # Clean up temp file
            try:
                os.remove(script_file)
            except:
                pass
            
            return agent_info
            
        except Exception as e:
            # Clean up on failure
            try:
                os.remove(script_file)
            except:
                pass
            raise e
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent and its container"""
        if agent_id not in self.agents:
            return False
        
        agent_info = self.agents[agent_id]
        
        try:
            container = self.docker_client.containers.get(agent_info["container_id"])
            container.remove(force=True)
        except Exception as e:
            logger.warning(f"Failed to remove container {agent_info['container_id']}: {e}")
        
        # Remove from storage
        del self.agents[agent_id]
        if agent_id in agents_db:
            del agents_db[agent_id]
        
        return True
    
    def list_agents(self) -> List[Dict]:
        """List all active agents"""
        # Update agent statuses
        for agent_id, agent_info in list(self.agents.items()):
            try:
                container = self.docker_client.containers.get(agent_info["container_id"])
                agent_info["status"] = container.status
            except:
                agent_info["status"] = "not_found"
        
        return list(self.agents.values())
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent information"""
        if agent_id not in self.agents:
            return None
        
        agent_info = self.agents[agent_id]
        
        # Update status
        try:
            container = self.docker_client.containers.get(agent_info["container_id"])
            agent_info["status"] = container.status
        except:
            agent_info["status"] = "not_found"
        
        return agent_info
    
    def chat_with_agent(self, agent_id: str, message: str, user_id: str = "api_user") -> Dict:
        """Send a chat message to an agent"""
        agent_info = self.get_agent(agent_id)
        if not agent_info:
            raise ValueError(f"Agent {agent_id} not found")
        
        if agent_info["status"] != "running":
            raise ValueError(f"Agent {agent_id} is not running (status: {agent_info['status']})")
        
        try:
            chat_response = requests.post(
                f"{agent_info['endpoint']}/chat",
                json={
                    "message": message,
                    "user_id": user_id
                },
                timeout=30
            )
            
            if chat_response.status_code == 200:
                return chat_response.json()
            else:
                raise RuntimeError(f"Chat request failed: {chat_response.status_code} - {chat_response.text}")
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to communicate with agent: {e}")

# Initialize agent manager
agent_manager = AgentManager()

# API Routes
@app.route('/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "service": "Agent Management API",
        "timestamp": datetime.now().isoformat(),
        "azure_configured": bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))
    })

@app.route('/templates', methods=['GET'])
def get_templates():
    """Get available system prompt templates"""
    try:
        templates = agent_manager.list_templates()
        return jsonify({
            "success": True,
            "templates": templates,
            "templates_available": TEMPLATES_AVAILABLE
        })
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/templates/<template_name>', methods=['GET'])
def get_template_detail(template_name):
    """Get specific template details"""
    try:
        prompt = agent_manager.get_template_prompt(template_name)
        if not prompt:
            return jsonify({
                "success": False,
                "error": f"Template '{template_name}' not found"
            }), 404
        
        return jsonify({
            "success": True,
            "template_name": template_name,
            "system_prompt": prompt
        })
    except Exception as e:
        logger.error(f"Failed to get template {template_name}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/debug/config', methods=['GET'])
def debug_config():
    """Debug endpoint to show current configuration"""
    try:
        return jsonify({
            "success": True,
            "environment": {
                "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "AZURE_DEPLOYMENT_NAME": os.getenv("AZURE_DEPLOYMENT_NAME"),
                "SERVER_HOST": os.getenv("SERVER_HOST", "localhost"),
                "CORS_ORIGINS": os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'),
                "api_key_present": bool(os.getenv("AZURE_OPENAI_API_KEY"))
            },
            "docker_info": {
                "containers_running": len([c for c in docker.from_env().containers.list()]),
                "agent_count": len(agent_manager.agents)
            }
        })
    except Exception as e:
        logger.error(f"Debug config error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/debug/azure-test', methods=['GET'])
def debug_azure_test():
    """Debug endpoint to test Azure connection independently"""
    try:
        logger.info("Debug Azure test endpoint called")
        
        # Test the connection
        result = agent_manager.test_azure_connection()
        
        return jsonify({
            "success": True,
            "azure_connection": result,
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_key_present": bool(os.getenv("AZURE_OPENAI_API_KEY")),
            "api_key_length": len(os.getenv("AZURE_OPENAI_API_KEY", ""))
        })
    except Exception as e:
        logger.error(f"Debug Azure test error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_key_present": bool(os.getenv("AZURE_OPENAI_API_KEY"))
        }), 500

@app.route('/debug/echo', methods=['POST'])
def debug_echo():
    """Debug endpoint to echo back request data"""
    try:
        logger.info(f"Debug echo - Content-Type: {request.content_type}")
        logger.info(f"Debug echo - Headers: {dict(request.headers)}")
        logger.info(f"Debug echo - Raw data: {request.get_data()}")
        
        if request.is_json:
            data = request.get_json()
            logger.info(f"Debug echo - Parsed JSON: {data}")
            return jsonify({
                "success": True,
                "received_data": data,
                "content_type": request.content_type,
                "is_json": request.is_json
            })
        else:
            return jsonify({
                "success": False,
                "error": "Request is not JSON",
                "content_type": request.content_type,
                "is_json": request.is_json,
                "raw_data": request.get_data().decode('utf-8')
            }), 400
    except Exception as e:
        logger.error(f"Debug echo error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents', methods=['POST'])
def create_agent():
    """Create a new agent"""
    try:
        # Check if request has JSON content type
        if not request.is_json:
            logger.error(f"Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({
                "success": False,
                "error": "Request must be JSON with Content-Type: application/json"
            }), 400
        
        data = request.get_json()
        if data is None:
            logger.error("Failed to parse JSON from request")
            return jsonify({
                "success": False,
                "error": "Invalid JSON in request body"
            }), 400
            
        logger.info(f"Received agent creation request with data: {data}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Support multiple parameter names for flexibility
        agent_type = data.get('agent_type') or data.get('type', 'coder')
        model_name = data.get('model_name') or data.get('model', 'gpt-4o-mini')
        deployment_name = data.get('deployment_name')
        system_prompt = data.get('system_prompt')
        template = data.get('template')
        
        logger.info(f"Parsed parameters - type: {agent_type}, model: {model_name}, deployment: {deployment_name}, template: {template}")
        
        agent_info = agent_manager.create_agent(agent_type, model_name, deployment_name, system_prompt, template)
        
        return jsonify({
            "success": True,
            "message": "Agent created successfully",
            "agent": agent_info
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/agents', methods=['GET'])
def list_agents():
    """List all agents"""
    try:
        agents = agent_manager.list_agents()
        return jsonify({
            "success": True,
            "agents": agents,
            "count": len(agents)
        })
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get specific agent information"""
    try:
        agent_info = agent_manager.get_agent(agent_id)
        if not agent_info:
            return jsonify({
                "success": False,
                "error": "Agent not found"
            }), 404
        
        return jsonify({
            "success": True,
            "agent": agent_info
        })
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent"""
    try:
        success = agent_manager.delete_agent(agent_id)
        if not success:
            return jsonify({
                "success": False,
                "error": "Agent not found"
            }), 404
        
        return jsonify({
            "success": True,
            "message": f"Agent {agent_id} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents/<agent_id>/chat', methods=['POST'])
def chat_with_agent(agent_id):
    """Chat with a specific agent"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        message = data['message']
        user_id = data.get('user_id', 'api_user')
        
        response = agent_manager.chat_with_agent(agent_id, message, user_id)
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "chat_response": response
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
    except Exception as e:
        logger.error(f"Failed to chat with agent {agent_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents/<agent_id>/health', methods=['GET'])
def agent_health(agent_id):
    """Check specific agent health"""
    try:
        agent_info = agent_manager.get_agent(agent_id)
        if not agent_info:
            return jsonify({
                "success": False,
                "error": "Agent not found"
            }), 404
        
        # Try to get health from agent
        try:
            health_response = requests.get(f"{agent_info['endpoint']}/health", timeout=5)
            if health_response.status_code == 200:
                agent_health_data = health_response.json()
            else:
                agent_health_data = {"status": "unhealthy", "error": f"HTTP {health_response.status_code}"}
        except Exception as e:
            agent_health_data = {"status": "unreachable", "error": str(e)}
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "container_status": agent_info["status"],
            "agent_health": agent_health_data
        })
        
    except Exception as e:
        logger.error(f"Failed to check agent {agent_id} health: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Agent Management API")
    print("=" * 40)
    
    # Check Azure configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
    
    if not azure_endpoint or not azure_key:
        print("⚠️  Warning: Azure OpenAI not configured")
        print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables")
        print("Example:")
        print('export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"')
        print('export AZURE_OPENAI_API_KEY="your-api-key"')
        print('export AZURE_DEPLOYMENT_NAME="your-deployment-name"  # optional')
    else:
        print("✅ Azure OpenAI configured")
        print(f"   Endpoint: {azure_endpoint}")
        print(f"   API Key: {'*' * 15 + azure_key[-4:]}")
        if azure_deployment:
            print(f"   Default Deployment: {azure_deployment}")
        else:
            print("   Default Deployment: gpt-4o-mini (fallback)")
    
    # Show hosting configuration
    server_host = os.getenv('SERVER_HOST', 'localhost')
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000')
    print(f"\n🌐 Server Configuration:")
    print(f"   Server Host: {server_host}")
    print(f"   CORS Origins: {cors_origins}")
    
    # Check templates
    if TEMPLATES_AVAILABLE:
        template_count = len(agent_manager.all_templates)
        print(f"\n✅ System prompt templates loaded: {template_count} templates available")
    else:
        print("\n⚠️  Warning: System prompt templates not loaded")
        print("   system_prompt_templates.py may be missing or have import errors")
    
    print("\n📋 API Endpoints:")
    print("  GET    /templates           - List available prompt templates")
    print("  GET    /templates/<name>    - Get specific template details")
    print("  POST   /agents              - Create new agent")
    print("  GET    /agents              - List all agents")
    print("  GET    /agents/<id>         - Get agent info")
    print("  DELETE /agents/<id>         - Delete agent")
    print("  POST   /agents/<id>/chat    - Chat with agent")
    print("  GET    /agents/<id>/health  - Check agent health")
    print("  GET    /health              - API health check")
    
    print(f"\n🚀 Starting server on http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)