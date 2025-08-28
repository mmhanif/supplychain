# Beer Distribution Game - User Interface Layer

## Overview

The user interface layer provides a web-based interface for the Beer Distribution Game, featuring real-time visualization, interactive controls, and comprehensive analytics. Built with FastAPI for the backend and vanilla JavaScript for the frontend, it offers both REST API and WebSocket communication for optimal responsiveness.

## Architecture

### Backend Components

#### 1. FastAPI Application (`simulation/web/app.py`)
- Main application server
- Serves static files and HTML
- Routes API and WebSocket connections
- CORS middleware for cross-origin requests

#### 2. REST API (`simulation/web/api/endpoints.py`)
Comprehensive endpoints for game management:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API root and status |
| `/api/scenarios` | GET | List available scenarios |
| `/api/scenarios/{id}` | GET | Get scenario details |
| `/api/scenarios` | POST | Create custom scenario |
| `/api/games` | POST | Create new game |
| `/api/games` | GET | List all games |
| `/api/games/{id}` | GET | Get game details |
| `/api/games/{id}/players` | POST | Add player to game |
| `/api/games/{id}/start` | POST | Start game |
| `/api/games/{id}/pause` | POST | Pause game |
| `/api/games/{id}/resume` | POST | Resume game |
| `/api/games/{id}/stop` | POST | Stop game |
| `/api/games/{id}/decisions` | POST | Submit player decision |
| `/api/games/{id}/state` | GET | Get current game state |
| `/api/games/{id}/results` | GET | Get game results |
| `/api/games/{id}/leaderboard` | GET | Get leaderboard |
| `/api/policies` | GET | List available policies |

#### 3. WebSocket Server (`simulation/web/api/websocket.py`)
Real-time bidirectional communication:

**ConnectionManager**: Manages WebSocket connections
- Game-based connection grouping
- Player-specific connections
- Broadcast capabilities
- Automatic cleanup on disconnect

**Message Types**:
- `connection`: Initial connection confirmation
- `game_state`: Full game state update
- `week_complete`: Weekly update with metrics
- `decision_request`: Request player decision
- `decision_confirmation`: Confirm submitted decision
- `game_ended`: Game completion notification
- `game_update`: General game updates
- `chat`: Player chat messages

**EventBus**: Internal event system for game-to-UI communication

### Frontend Components

#### 1. HTML Template (`templates/index.html`)
Single-page application structure:
- **Header**: Game info and status
- **Supply Chain Visualization**: Node states and connections
- **Performance Metrics**: Real-time KPIs
- **Control Panel**: Game setup and play controls
- **Analytics Charts**: Time-series visualizations
- **Results Modal**: End-game statistics

#### 2. CSS Styling (`static/css/style.css`)
Modern, responsive design:
- Gradient background
- Card-based layout
- Color-coded supply chain nodes
- Animated interactions
- Responsive grid system
- Modal overlays

#### 3. JavaScript Application (`static/js/game.js`)
Complete game client:
- **BeerGame Class**: Main application controller
- **API Integration**: REST and WebSocket communication
- **State Management**: Game and UI state
- **Chart Management**: Real-time data visualization
- **Event Handling**: User interactions and server events

## Features

### 1. Supply Chain Visualization
- **Visual Network**: Four-tier supply chain display
- **Node States**: Real-time inventory, backlog, orders
- **Color Coding**: Visual distinction between nodes
- **Interactive**: Hover effects and animations

### 2. Real-Time Updates
- **WebSocket Communication**: Instant state updates
- **Event Notifications**: Player actions and game events
- **Message System**: Timestamped event log
- **Connection Status**: Live connection indicators

### 3. Interactive Controls
- **Game Setup**: Scenario selection, player configuration
- **Order Submission**: Quantity input and validation
- **Game Management**: Start, pause, resume, stop
- **Role Selection**: Choose supply chain position

### 4. Analytics Dashboard
- **Time-Series Charts**: Using Chart.js
- **Multiple Views**: Inventory, costs, orders
- **Tab Navigation**: Switch between metrics
- **Real-Time Updates**: Live chart updates

### 5. Performance Metrics
- **Total Cost**: Running total and average
- **Service Level**: Fill rate percentage
- **Bullwhip Ratio**: Demand amplification metric
- **Leaderboard**: Player rankings and scores

## User Flow

### 1. Game Setup
```
Select Scenario → Enter Name → Choose Role → Create Game
```

### 2. Gameplay
```
View State → Submit Order → Receive Updates → Monitor Metrics
```

### 3. Game Completion
```
Game Ends → View Results → Check Leaderboard → Save/Export
```

## WebSocket Protocol

### Client Messages
```javascript
// Request game state
{
    "type": "request_state"
}

// Submit decision
{
    "type": "decision",
    "order_quantity": 10
}

// Send chat message
{
    "type": "chat",
    "message": "Hello team!"
}
```

### Server Messages
```javascript
// Game state update
{
    "type": "game_state",
    "state": {
        "current_week": 5,
        "metrics": {...},
        "nodes": {...}
    }
}

// Week completion
{
    "type": "week_complete",
    "week": 5,
    "metrics": {...},
    "node_states": {...}
}

// Decision request
{
    "type": "decision_request",
    "week": 5,
    "node_state": {...}
}
```

## Running the Web Server

### Quick Start
```bash
# Install dependencies
uv pip install fastapi uvicorn websockets pydantic

# Run the server
uv run python run_web_server.py
```

### Direct Execution
```bash
python -m simulation.web.app
```

### Development Mode
```bash
uvicorn simulation.web.app:app --reload --port 8000
```

### Production Deployment
```bash
uvicorn simulation.web.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Usage Examples

### Create and Start a Game
```javascript
// 1. Create game
const gameResponse = await fetch('/api/games', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        scenario_id: 'classic',
        max_weeks: 52
    })
});
const game = await gameResponse.json();

// 2. Add player
const playerResponse = await fetch(`/api/games/${game.game_id}/players`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'Alice',
        role: 'retailer',
        is_human: true
    })
});

// 3. Start game
await fetch(`/api/games/${game.game_id}/start`, {method: 'POST'});
```

### Connect WebSocket
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${gameId}/${playerId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleGameUpdate(data);
};

// Submit decision via WebSocket
ws.send(JSON.stringify({
    type: 'decision',
    order_quantity: 10
}));
```

## Browser Compatibility

- **Chrome**: Full support (recommended)
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support
- **Mobile Browsers**: Responsive design support

## Performance Considerations

### Optimization Strategies
1. **WebSocket Pooling**: Reuse connections
2. **Data Batching**: Group updates
3. **Chart Throttling**: Limit update frequency
4. **Message Compression**: Reduce payload size
5. **Lazy Loading**: Load resources on demand

### Scalability
- **Multiple Games**: Concurrent game sessions
- **Connection Management**: Automatic cleanup
- **State Caching**: Reduce computation
- **Load Balancing**: Multiple server instances

## Security

### Implemented Measures
- **CORS Configuration**: Controlled access
- **Input Validation**: Pydantic models
- **WebSocket Authentication**: Player ID verification
- **Rate Limiting**: (Can be added)
- **HTTPS Support**: Production deployment

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify port 8000 is available
   - Ensure JavaScript is enabled

2. **Charts Not Displaying**
   - Check Chart.js CDN availability
   - Verify canvas element exists
   - Check console for errors

3. **Game Not Starting**
   - Ensure all players added
   - Check game status
   - Verify simulation running

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Internationalization
2. **Mobile App**: Native mobile clients
3. **Voice Commands**: Speech recognition
4. **AR Visualization**: Augmented reality view
5. **AI Assistance**: Hints and recommendations
6. **Social Features**: Friends, teams, tournaments
7. **Data Export**: CSV, Excel, PDF reports
8. **Replay System**: Game recording and playback

### API Extensions
- GraphQL support
- Server-Sent Events
- gRPC for high-performance
- OAuth2 authentication
- API versioning

## Dependencies

### Backend
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `websockets`: WebSocket support
- `pydantic`: Data validation

### Frontend
- `Chart.js`: Data visualization (CDN)
- `Font Awesome`: Icons (CDN)
- Vanilla JavaScript (no framework dependencies)

## Summary

The user interface layer provides a complete, modern web interface for the Beer Distribution Game with:

✅ **Real-time Updates**: WebSocket-based live communication
✅ **Interactive Visualization**: Supply chain network display
✅ **Comprehensive Analytics**: Charts and metrics
✅ **Responsive Design**: Works on all devices
✅ **REST + WebSocket**: Dual communication protocols
✅ **Production Ready**: Scalable architecture

The implementation follows the architecture specification from `beer_game_architecture.md` and integrates seamlessly with the simulation engine and game logic layers to provide a complete gaming experience.
