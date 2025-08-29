# Agent Swarm Web Dashboard

A real-time monitoring and control dashboard for the Agent Swarm system.

## Features

- **Real-time Monitoring**: Live performance metrics and system status
- **Session Management**: View, analyze, and replay agent sessions
- **WebSocket Integration**: Real-time event streaming and updates
- **Agent Control**: Monitor and manage individual agent performance
- **Analytics**: Historical metrics and trend analysis
- **Error Tracking**: Comprehensive error logging and analysis
- **Dark Mode**: Full dark mode support

## Architecture

```
web/
├── web_server.py           # FastAPI backend server
├── dashboard/              # React frontend application
│   ├── src/
│   │   ├── services/       # API and WebSocket clients
│   │   ├── store/          # Zustand state management
│   │   ├── components/     # Reusable UI components
│   │   └── pages/          # Dashboard pages
├── lib/                    # Backend libraries
│   ├── event_streamer.py   # Event streaming system
│   └── ws_events.py        # WebSocket event handlers
└── api/                    # API endpoint modules
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation

### Automatic Setup (Recommended)

#### Windows:
```bash
cd web
start_dashboard.bat
```

#### Mac/Linux:
```bash
cd web
chmod +x start_dashboard.sh
./start_dashboard.sh
```

#### Python Script (Cross-platform):
```bash
cd web
python start_dashboard.py
```

### Manual Setup

1. **Install Backend Dependencies**:
```bash
cd web
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**:
```bash
cd web/dashboard
npm install
```

3. **Start Backend Server**:
```bash
cd web
python web_server.py
```

4. **Start Frontend Development Server** (in a new terminal):
```bash
cd web/dashboard
npm run dev
```

5. **Open Dashboard**:
Navigate to http://localhost:5173 in your browser

## Usage

### Dashboard Views

1. **Overview**: System-wide metrics and status
2. **Sessions**: View and manage agent sessions
3. **Monitoring**: Real-time performance tracking
4. **Analytics**: Historical data and trends
5. **Agents**: Individual agent management
6. **Errors**: Error tracking and analysis

### API Documentation

The FastAPI backend provides interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### WebSocket Connection

Connect to the WebSocket endpoint for real-time updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

## Configuration

Edit `config.yaml` to customize:
- Server settings
- WebSocket parameters
- Authentication configuration
- Monitoring intervals

## Development

### Backend Development

The backend uses FastAPI with WebSocket support:

```python
# Example: Adding a new API endpoint
@app.get("/api/custom")
async def custom_endpoint():
    return {"data": "custom"}
```

### Frontend Development

The frontend uses React with TypeScript and Vite:

```typescript
// Example: Creating a new component
import React from 'react';

const CustomComponent: React.FC = () => {
  return <div>Custom Component</div>;
};
```

### State Management

Using Zustand for state management:

```typescript
// Access the store
import useDashboardStore from '../store/dashboardStore';

const Component = () => {
  const { sessions, fetchSessions } = useDashboardStore();
  // Use state and actions
};
```

## WebSocket Events

The dashboard supports various real-time events:

- `session.started` - New session started
- `session.completed` - Session finished
- `agent.started` - Agent execution started
- `agent.completed` - Agent execution finished
- `performance.update` - Performance metrics update
- `error.occurred` - Error detected
- `cost.update` - Cost tracking update

## Production Deployment

### Backend Deployment

1. Set environment variables:
```bash
export ANTHROPIC_API_KEY=your-key
```

2. Run with production server:
```bash
uvicorn web_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Build

1. Build for production:
```bash
cd dashboard
npm run build
```

2. Serve the `dist` folder with any static file server

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Connection Issues
- Ensure both backend and frontend servers are running
- Check firewall settings for ports 8000 and 5173
- Verify CORS settings in `web_server.py`

### WebSocket Issues
- Check browser console for connection errors
- Ensure WebSocket endpoint is accessible
- Verify event subscriptions are correct

### Performance Issues
- Adjust `update_interval` in config
- Limit event buffer size
- Use pagination for large datasets

## Security Considerations

- Always use HTTPS in production
- Implement proper authentication
- Validate all user inputs
- Use environment variables for secrets
- Enable CORS only for trusted origins

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## License

Part of the Agent Swarm project

---

For more information about the Agent Swarm system, see the main project documentation.