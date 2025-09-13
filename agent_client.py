#!/usr/bin/env python3
"""
Simple client to interact with the Agent Management API
"""

import requests
import json
import time
import sys

class AgentAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
    
    def health_check(self):
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_templates(self):
        """Get available templates"""
        try:
            response = requests.get(f"{self.base_url}/templates")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_template_detail(self, template_name):
        """Get specific template details"""
        try:
            response = requests.get(f"{self.base_url}/templates/{template_name}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_agent(self, agent_type="coder", model_name="gpt-4o-mini", system_prompt=None, template=None):
        """Create a new agent"""
        try:
            payload = {"agent_type": agent_type, "model_name": model_name}
            if template:
                payload["template"] = template
            elif system_prompt:
                payload["system_prompt"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/agents",
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_agents(self):
        """List all agents"""
        try:
            response = requests.get(f"{self.base_url}/agents")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_agent(self, agent_id):
        """Get specific agent information"""
        try:
            response = requests.get(f"{self.base_url}/agents/{agent_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def delete_agent(self, agent_id):
        """Delete an agent"""
        try:
            response = requests.delete(f"{self.base_url}/agents/{agent_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat_with_agent(self, agent_id, message, user_id="client_user"):
        """Chat with an agent"""
        try:
            response = requests.post(
                f"{self.base_url}/agents/{agent_id}/chat",
                json={"message": message, "user_id": user_id}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def agent_health(self, agent_id):
        """Check agent health"""
        try:
            response = requests.get(f"{self.base_url}/agents/{agent_id}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def demo():
    """Run a demonstration of the API"""
    client = AgentAPIClient()
    
    print("🚀 Agent API Client Demo")
    print("=" * 30)
    
    # Health check
    print("\n1. API Health Check:")
    health = client.health_check()
    print_json(health)
    
    if health.get("error"):
        print("❌ API is not responding. Make sure the API server is running.")
        return
    
    # Create an agent
    print("\n2. Creating a new agent...")
    create_result = client.create_agent("coder", "gpt-4o-mini")
    print_json(create_result)
    
    if not create_result.get("success"):
        print("❌ Failed to create agent")
        return
    
    agent_id = create_result["agent"]["agent_id"]
    print(f"✅ Agent created with ID: {agent_id}")
    
    # Wait a moment
    print("\n⏳ Waiting for agent to be ready...")
    time.sleep(3)
    
    # List agents
    print("\n3. Listing all agents:")
    agents_list = client.list_agents()
    print_json(agents_list)
    
    # Get specific agent
    print(f"\n4. Getting agent {agent_id[:8]}... details:")
    agent_details = client.get_agent(agent_id)
    print_json(agent_details)
    
    # Check agent health
    print(f"\n5. Checking agent {agent_id[:8]}... health:")
    agent_health_data = client.agent_health(agent_id)
    print_json(agent_health_data)
    
    # Chat with agent
    print(f"\n6. Chatting with agent {agent_id[:8]}...:")
    chat_message = "Write a Python function to calculate fibonacci numbers"
    print(f"Message: {chat_message}")
    
    chat_result = client.chat_with_agent(agent_id, chat_message)
    print("Response:")
    print_json(chat_result)
    
    # Ask user if they want to delete the agent
    print(f"\n7. Agent Management:")
    delete_choice = input(f"Delete agent {agent_id[:8]}...? (y/n): ").lower().strip()
    
    if delete_choice == 'y':
        print("Deleting agent...")
        delete_result = client.delete_agent(agent_id)
        print_json(delete_result)
    else:
        print(f"Agent {agent_id[:8]}... left running")
        print(f"You can delete it later with: DELETE /agents/{agent_id}")

def interactive_mode():
    """Interactive mode for testing the API"""
    client = AgentAPIClient()
    
    print("🎮 Interactive Agent API Client")
    print("=" * 35)
    print("Commands:")
    print("  health          - Check API health")
    print("  templates       - List available templates")
    print("  template <name> - Get template details")
    print("  create          - Create new agent")
    print("  create <template> - Create agent with template")
    print("  list            - List all agents")
    print("  get <id>        - Get agent details")
    print("  chat <id>       - Chat with agent")
    print("  delete <id>     - Delete agent")
    print("  health <id>     - Check agent health")
    print("  quit            - Exit")
    print()
    
    while True:
        try:
            command = input("agent-api> ").strip().split()
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == "quit":
                break
            elif cmd == "health":
                if len(command) == 1:
                    result = client.health_check()
                else:
                    result = client.agent_health(command[1])
                print_json(result)
            elif cmd == "templates":
                result = client.get_templates()
                print_json(result)
            elif cmd == "template":
                if len(command) < 2:
                    print("Usage: template <template_name>")
                    continue
                result = client.get_template_detail(command[1])
                print_json(result)
            elif cmd == "create":
                if len(command) > 1:
                    # Create with template
                    template_name = command[1]
                    result = client.create_agent(template=template_name)
                else:
                    # Create default agent
                    result = client.create_agent()
                print_json(result)
            elif cmd == "list":
                result = client.list_agents()
                print_json(result)
            elif cmd == "get":
                if len(command) < 2:
                    print("Usage: get <agent_id>")
                    continue
                result = client.get_agent(command[1])
                print_json(result)
            elif cmd == "delete":
                if len(command) < 2:
                    print("Usage: delete <agent_id>")
                    continue
                result = client.delete_agent(command[1])
                print_json(result)
            elif cmd == "chat":
                if len(command) < 2:
                    print("Usage: chat <agent_id>")
                    continue
                agent_id = command[1]
                message = input("Message: ")
                result = client.chat_with_agent(agent_id, message)
                print_json(result)
            else:
                print(f"Unknown command: {cmd}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        demo()