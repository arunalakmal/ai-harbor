// API Configuration - Read from environment or use auto-detection fallback
// Priority: Environment variable > Auto-detection > Default
const API_BASE_URL = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    console.log(`Frontend running on: ${protocol}//${hostname}:${window.location.port}`);
    
    // Check if API_BASE_URL is provided via environment/build process
    // This can be set during build or injected via environment
    const envApiUrl = window.ENV?.API_BASE_URL || process.env.API_BASE_URL;
    
    if (envApiUrl) {
        console.log(`🔧 Using environment API URL: ${envApiUrl}`);
        return envApiUrl;
    }
    
    // Fallback to auto-detection
    console.log('📡 No environment API URL found, using auto-detection...');
    
    // Local development detection
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        console.log('🏠 Local development mode detected');
        return 'http://localhost:8080';  // Backend always on port 8080 locally
    }
    
    // Production mode - backend on same host, port 8080
    const backendUrl = `${protocol}//${hostname}:8080`;
    console.log(`🌐 Production mode detected - Backend URL: ${backendUrl}`);
    return backendUrl;
})();

console.log(`✅ Final API Base URL: ${API_BASE_URL}`);

// Global state
let agents = [];
let templates = [];
let currentChatAgent = null;

// DOM Elements
const elements = {
    connectionStatus: document.getElementById('connection-status'),
    createAgentBtn: document.getElementById('create-agent-btn'),
    refreshAgentsBtn: document.getElementById('refresh-agents-btn'),
    agentsList: document.getElementById('agents-list'),
    chatSection: document.getElementById('chat-section'),
    closeChatBtn: document.getElementById('close-chat-btn'),
    chatMessages: document.getElementById('chat-messages'),
    messageInput: document.getElementById('message-input'),
    sendMessageBtn: document.getElementById('send-message-btn'),
    currentAgentInfo: document.getElementById('current-agent-info'),
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container'),
    agentType: document.getElementById('agent-type'),
    modelName: document.getElementById('model-name'),
    deploymentName: document.getElementById('deployment-name'),
    templateSelect: document.getElementById('template-select'),
    customPrompt: document.getElementById('custom-prompt')
};

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await checkConnection();
    await loadTemplates();
    await loadAgents();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    elements.createAgentBtn.addEventListener('click', createAgent);
    elements.refreshAgentsBtn.addEventListener('click', loadAgents);
    elements.closeChatBtn.addEventListener('click', closeChat);
    elements.sendMessageBtn.addEventListener('click', sendMessage);
    
    // Send message on Enter (but allow Shift+Enter for new lines)
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        console.log(`Making API call to: ${API_BASE_URL}${endpoint}`);
        console.log('Request options:', options);
        console.log('Request body:', options.body);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', [...response.headers.entries()]);
        
        const responseText = await response.text();
        console.log('Raw response:', responseText);
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (parseError) {
            console.error('Failed to parse response as JSON:', parseError);
            throw new Error(`Invalid JSON response: ${responseText.substring(0, 100)}...`);
        }
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

async function checkConnection() {
    try {
        console.log('Checking API connection...');
        const response = await apiCall('/health');
        console.log('Health check response:', response);
        
        if (response.status === 'healthy') {
            elements.connectionStatus.textContent = 'Connected';
            elements.connectionStatus.className = 'status-connected';
            console.log('API connection successful');
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        console.error('API connection failed:', error);
        elements.connectionStatus.textContent = 'Disconnected';
        elements.connectionStatus.className = 'status-disconnected';
        showToast(`Failed to connect to API: ${error.message}`, 'error');
    }
}

async function loadTemplates() {
    try {
        const response = await apiCall('/templates');
        if (response.success) {
            templates = response.templates.all_templates || [];
            populateTemplateSelect();
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

function populateTemplateSelect() {
    elements.templateSelect.innerHTML = '<option value="">-- No Template --</option>';
    templates.forEach(template => {
        const option = document.createElement('option');
        option.value = template;
        option.textContent = template.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        elements.templateSelect.appendChild(option);
    });
}

async function loadAgents() {
    showLoading(true);
    try {
        const response = await apiCall('/agents');
        if (response.success) {
            agents = response.agents || [];
            renderAgents();
        } else {
            throw new Error(response.error || 'Failed to load agents');
        }
    } catch (error) {
        console.error('Failed to load agents:', error);
        showToast('Failed to load agents', 'error');
        agents = [];
        renderAgents();
    } finally {
        showLoading(false);
    }
}

async function createAgent() {
    const agentData = {
        agent_type: elements.agentType.value,  // Use agent_type instead of type
        model_name: elements.modelName.value   // Use model_name instead of model
    };

    // Add deployment name if provided
    if (elements.deploymentName.value.trim()) {
        agentData.deployment_name = elements.deploymentName.value.trim();
    }

    // Add template or custom prompt
    if (elements.templateSelect.value) {
        agentData.template = elements.templateSelect.value;
    } else if (elements.customPrompt.value.trim()) {
        agentData.system_prompt = elements.customPrompt.value.trim();
    }

    console.log('Creating agent with data:', agentData);
    showLoading(true);
    
    try {
        const response = await apiCall('/agents', {
            method: 'POST',
            body: JSON.stringify(agentData)
        });

        console.log('Agent creation response:', response);

        if (response.success) {
            showToast('Agent created successfully!', 'success');
            elements.customPrompt.value = '';
            elements.templateSelect.value = '';
            elements.deploymentName.value = '';
            await loadAgents();
        } else {
            throw new Error(response.error || 'Failed to create agent');
        }
    } catch (error) {
        console.error('Failed to create agent:', error);
        showToast(`Failed to create agent: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) {
        return;
    }

    showLoading(true);
    try {
        const response = await apiCall(`/agents/${agentId}`, {
            method: 'DELETE'
        });

        if (response.success) {
            showToast('Agent deleted successfully!', 'success');
            if (currentChatAgent && currentChatAgent.agent_id === agentId) {
                closeChat();
            }
            await loadAgents();
        } else {
            throw new Error(response.error || 'Failed to delete agent');
        }
    } catch (error) {
        console.error('Failed to delete agent:', error);
        showToast(`Failed to delete agent: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function startChat(agent) {
    currentChatAgent = agent;
    elements.currentAgentInfo.textContent = `${agent.agent_name} (${agent.agent_type})`;
    elements.chatMessages.innerHTML = '';
    elements.chatSection.style.display = 'block';
    elements.chatSection.scrollIntoView({ behavior: 'smooth' });
    
    // Add welcome message
    addChatMessage('agent', `Hello! I'm your ${agent.agent_type} agent. How can I help you today?`, new Date());
}

function closeChat() {
    currentChatAgent = null;
    elements.chatSection.style.display = 'none';
    elements.messageInput.value = '';
}

async function sendMessage() {
    if (!currentChatAgent) return;
    
    const message = elements.messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addChatMessage('user', message, new Date());
    elements.messageInput.value = '';

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await apiCall(`/agents/${currentChatAgent.agent_id}/chat`, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                user_id: 'web_user'
            })
        });

        removeTypingIndicator(typingId);

        if (response.success) {
            addChatMessage('agent', response.chat_response.response, new Date());
        } else {
            throw new Error(response.error || 'Failed to send message');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        console.error('Failed to send message:', error);
        
        // Check if this is an Azure connection error
        if (error.message.includes('Name or service not known') || 
            error.message.includes('Azure OpenAI Network Error')) {
            
            // Get deployment info from current agent
            const deploymentInfo = currentChatAgent.deployment_name ? 
                `\nCurrent deployment: ${currentChatAgent.deployment_name}` : '';
            
            addChatMessage('agent', 
                `🔧 **Azure Connection Issue**\n\n` +
                `Your Azure OpenAI endpoint appears to be incorrect.${deploymentInfo}\n\n` +
                `**To fix this:**\n` +
                `1. Go to Azure Portal → Azure OpenAI\n` +
                `2. Find your resource name (not deployment name)\n` +
                `3. Set: export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE-NAME.openai.azure.com/"\n` +
                `4. Restart the API server\n\n` +
                `Note: Make sure you're using the resource endpoint, not the deployment name in the URL.`, 
                new Date(), true);
        } else {
            addChatMessage('agent', `❌ Error: ${error.message}`, new Date(), true);
        }
    }
}

// UI Helper Functions
function renderAgents() {
    if (agents.length === 0) {
        elements.agentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-robot"></i>
                <h3>No Agents Yet</h3>
                <p>Create your first agent to get started!</p>
            </div>
        `;
        return;
    }

    elements.agentsList.innerHTML = agents.map(agent => `
        <div class="agent-card">
            <div class="agent-header">
                <div class="agent-title">${agent.agent_name}</div>
                <div class="agent-status status-${agent.status === 'running' ? 'running' : 'stopped'}">
                    ${agent.status}
                </div>
            </div>
            <div class="agent-info">
                <p><strong>Type:</strong> ${agent.agent_type}</p>
                <p><strong>Model:</strong> ${agent.model_name}</p>
                <p><strong>Created:</strong> ${new Date(agent.created_at).toLocaleString()}</p>
                ${agent.template_used ? `<p><strong>Template:</strong> ${agent.template_used}</p>` : ''}
                <p><strong>Endpoint:</strong> ${agent.endpoint}</p>
            </div>
            <div class="agent-actions">
                <button class="btn btn-success btn-small" onclick="startChat(${JSON.stringify(agent).replace(/"/g, '&quot;')})">
                    <i class="fas fa-comments"></i> Chat
                </button>
                <button class="btn btn-secondary btn-small" onclick="checkAgentHealth('${agent.agent_id}')">
                    <i class="fas fa-heartbeat"></i> Health
                </button>
                <button class="btn btn-danger btn-small" onclick="deleteAgent('${agent.agent_id}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

function addChatMessage(sender, message, timestamp, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message message-${sender}`;
    
    const bubbleClass = isError ? 'message-bubble error' : 'message-bubble';
    
    // Format message - handle basic markdown for error messages
    let formattedMessage = escapeHtml(message);
    if (isError && message.includes('**')) {
        // Simple markdown formatting for bold text
        formattedMessage = formattedMessage.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    }
    formattedMessage = formattedMessage.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="${bubbleClass}">${formattedMessage}</div>
        <div class="message-info">${timestamp.toLocaleTimeString()}</div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'chat-message message-agent';
    typingDiv.innerHTML = `
        <div class="message-bubble">
            <i class="fas fa-ellipsis-h fa-pulse"></i> Typing...
        </div>
    `;
    
    elements.chatMessages.appendChild(typingDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingDiv = document.getElementById(typingId);
    if (typingDiv) {
        typingDiv.remove();
    }
}

async function checkAgentHealth(agentId) {
    try {
        const response = await apiCall(`/agents/${agentId}/health`);
        if (response.success) {
            const status = response.agent_health.status || 'unknown';
            showToast(`Agent health: ${status}`, status === 'healthy' ? 'success' : 'error');
        } else {
            throw new Error(response.error || 'Failed to check health');
        }
    } catch (error) {
        console.error('Failed to check agent health:', error);
        showToast(`Health check failed: ${error.message}`, 'error');
    }
}

function showLoading(show) {
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
    
    // Allow manual removal
    toast.addEventListener('click', () => {
        toast.remove();
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally available for onclick handlers
window.startChat = startChat;
window.deleteAgent = deleteAgent;
window.checkAgentHealth = checkAgentHealth;