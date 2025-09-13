# Containerized Agents Frontend

A modern web interface for managing containerized Azure OpenAI agents.

## Features

- 🚀 **Agent Management**: Create, list, and delete agents with an intuitive interface
- 💬 **Real-time Chat**: Chat with your agents directly in the browser
- 📋 **Template Support**: Use predefined templates or create custom system prompts
- 📊 **Health Monitoring**: Check agent status and health
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🎨 **Modern UI**: Clean, gradient-based design with smooth animations

## Screenshots

### Main Dashboard
- Clean overview of all active agents
- Easy agent creation with templates
- Real-time connection status

### Chat Interface
- Real-time messaging with agents
- Clean message bubbles
- Typing indicators
- Message timestamps

### Agent Cards
- Agent status indicators
- Quick action buttons (Chat, Health, Delete)
- Agent details (type, model, endpoint)

## Getting Started

### Prerequisites

1. **API Server Running**: Make sure your `agent_api.py` is running on `http://localhost:8080`
2. **CORS Enabled**: The API already has CORS support enabled
3. **Modern Browser**: Chrome, Firefox, Safari, or Edge

### Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Serve the files**: You can use any web server. Here are a few options:

   **Option A: Python HTTP Server**
   ```bash
   python -m http.server 3000
   ```

   **Option B: Node.js HTTP Server**
   ```bash
   npx http-server -p 3000
   ```

   **Option C: PHP Built-in Server**
   ```bash
   php -S localhost:3000
   ```

   **Option D: Visual Studio Code Live Server**
   - Install the "Live Server" extension
   - Right-click on `index.html` and select "Open with Live Server"

3. **Access the application**:
   ```
   http://localhost:3000
   ```

## Usage

### Creating Agents

1. **Select Agent Type**: Choose from coder, general, analyzer, or creative
2. **Choose Model**: Select your preferred GPT model
3. **Use Template (Optional)**: Pick from predefined templates for specialized roles
4. **Custom Prompt (Optional)**: Write your own system prompt
5. **Click Create**: The agent will be created and appear in the agents list

### Chatting with Agents

1. **Click Chat Button**: On any running agent card
2. **Type Message**: Enter your message in the chat input
3. **Send**: Press Enter or click the send button
4. **Continue Conversation**: Chat naturally with your agent

### Managing Agents

- **Health Check**: Click the health button to check if an agent is responding
- **Delete Agent**: Click the delete button to remove an agent and its container
- **Refresh List**: Click refresh to update the agents list

## Features in Detail

### Connection Status
- **Green "Connected"**: API is accessible and healthy
- **Red "Disconnected"**: Cannot reach the API server

### Agent Status
- **Running**: Agent is active and ready to chat
- **Stopped**: Agent container is not running

### Templates
- Automatically loads available templates from the API
- Dropdown selection for easy access
- Templates override custom prompts when selected

### Error Handling
- Toast notifications for success/error messages
- Graceful fallbacks when API is unavailable
- Clear error messages for troubleshooting

## Configuration

### API URL
If your API is running on a different port or host, update the `API_BASE_URL` in `app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8080';  // Change this if needed
```

### Styling
- Modify `styles.css` to customize the appearance
- Color scheme uses CSS custom properties for easy theming
- Responsive breakpoints defined for mobile optimization

## File Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # All styling and animations
├── app.js             # JavaScript application logic
└── README.md          # This file
```

## Browser Compatibility

- **Chrome**: 70+
- **Firefox**: 65+
- **Safari**: 12+
- **Edge**: 79+

## Development

### Adding New Features

1. **API Calls**: Add new functions to the API section in `app.js`
2. **UI Components**: Add HTML structure and CSS styling
3. **Event Handlers**: Wire up user interactions

### Customizing Styles

The CSS uses CSS Grid and Flexbox for layouts, making it easy to modify:
- Colors are defined with CSS custom properties
- Responsive design uses media queries
- Animations use CSS transitions and transforms

## Troubleshooting

### "Disconnected" Status
- Ensure `agent_api.py` is running on port 8080
- Check if CORS is enabled in the API
- Verify no firewall is blocking the connection

### Agents Not Loading
- Check browser console for error messages
- Verify API health endpoint returns success
- Ensure Docker is running for agent containers

### Chat Not Working
- Confirm the agent status is "running"
- Check if the agent container is healthy
- Look for error messages in chat or console

## Future Enhancements

Potential features to add:
- **File Upload**: Support for document uploads to agents
- **Chat History**: Persistent conversation history
- **Agent Templates**: Save and share custom agent configurations
- **Real-time Updates**: WebSocket support for live updates
- **Dark Mode**: Toggle between light and dark themes
- **Export Chat**: Download conversation transcripts

# Frontend Configuration Examples

This file shows various ways to configure the frontend backend URL.

## Quick Start

```bash
# Make script executable (first time only)
chmod +x frontend/configure.sh

# Configure for local development
cd frontend
./configure.sh local

# Start backend
python agent_api.py

# Start frontend
python -m http.server 3000
```

## Environment-Specific Examples

### Local Development
```bash
cd frontend
./configure.sh local
# Result: API_BASE_URL = 'http://localhost:8080'
```

### Local Network Testing
```bash
cd frontend
./configure.sh network 192.168.1.100
# Result: API_BASE_URL = 'http://192.168.1.100:8080'
```

### Production Same-Host
```bash
cd frontend
./configure.sh production myapp.com
# Result: API_BASE_URL = 'https://myapp.com:8080'
```

### Custom API Server
```bash
cd frontend
./configure.sh custom https://api.mycompany.com
# Result: API_BASE_URL = 'https://api.mycompany.com'
```

### Auto-Detection Mode
```bash
cd frontend
./configure.sh auto
# Result: API_BASE_URL = undefined (uses auto-detection)
```

## Manual Configuration

Edit `frontend/config.js` directly:

```javascript
window.ENV = {
    API_BASE_URL: 'http://your-backend-url:8080'
};
```

## Build-Time Configuration

```bash
# Set environment variable
export API_BASE_URL=https://api.myapp.com

# Frontend will use this during runtime
```

## Verification

Check configuration in browser console:
```javascript
console.log('API URL:', API_BASE_URL);
console.log('Config:', window.ENV);
```