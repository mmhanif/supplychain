# Beer Distribution Game Simulation Architecture

## Overview
This document outlines the high-level architecture for implementing the Beer Distribution Game using Python's SimPy module with an interactive web-based user interface.

## Core Components

### 1. Simulation Engine Layer

#### SimPy Environment Core
- The central simulation environment that manages discrete event scheduling
- Controls simulation time and event processing
- Manages the simulation clock and time advancement

#### Supply Chain Entities
- Classes for each node in the supply chain:
  - Retailer
  - Wholesaler
  - Distributor
  - Factory
- All inherit from a base `SupplyChainNode` class
- Each node maintains inventory, processes orders, and manages shipments

#### Order/Inventory Management
- Logic for order placement and processing
- Fulfillment tracking and scheduling
- Backlog management for unfulfilled orders
- Inventory holding and replenishment logic

#### Metrics Collector
- Captures time-series data at each simulation step
- Tracks key performance indicators:
  - Inventory levels
  - Order quantities
  - Backlog amounts
  - Costs (holding, stockout)
  - Service levels

### 2. Game Logic Layer

#### Game Controller
- Manages game rules and win conditions
- Calculates costs:
  - Holding costs per unit inventory
  - Stockout/backlog penalties
  - Total supply chain costs
- Determines game end conditions
- Tracks player performance

#### Policy Manager
- Implements different ordering policies:
  - Human-controlled (manual input)
  - Base-stock policy
  - Economic Order Quantity (EOQ)
  - (s,S) inventory policy
  - Custom AI/ML-based policies
- Allows switching between policies during setup

#### Scenario Manager
- Handles different demand patterns:
  - Constant demand
  - Step change
  - Random variation
  - Seasonal patterns
- Manages initial conditions and game parameters
- Supports custom scenario creation

### 3. User Interface Layer

#### Web-Based Frontend
- HTML/CSS/JavaScript with modern framework
- Responsive design for various screen sizes
- Real-time updates without page refresh

#### Visualization Components

**Supply Chain Network Diagram**
- Visual representation of the four-tier supply chain
- Real-time state display for each node
- Animation of order/shipment flows

**Real-time Charts**
- Time-series plots for:
  - Inventory levels by node
  - Orders and shipments
  - Costs over time
  - Bullwhip effect visualization
- Interactive chart controls (zoom, pan, data selection)

**Control Panel**
- Parameter configuration interface
- Simulation controls (start, pause, stop, reset)
- Speed adjustment for simulation playback
- Manual order input for human players

### 4. Communication Layer

#### WebSocket Server
- Enables real-time bidirectional communication
- Pushes simulation updates to UI
- Receives user commands and inputs
- Maintains persistent connections during simulation

#### REST API
- Configuration endpoints:
  - `/api/config` - Set simulation parameters
  - `/api/scenarios` - List and select scenarios
  - `/api/start` - Initialize simulation
  - `/api/stop` - Terminate simulation
- Data retrieval endpoints:
  - `/api/results` - Get simulation results
  - `/api/history` - Retrieve historical data

#### Event Bus
- Publishes simulation events:
  - Order placed
  - Delivery received
  - Week completed
  - Cost updated
- Allows UI components to subscribe to relevant events

## Technology Stack Recommendation

### Backend
- **Python 3.8+** - Core programming language
- **SimPy** - Discrete event simulation library
- **FastAPI** or **Flask** - Web framework
- **WebSockets** - Via `websockets` library or Socket.IO
- **SQLite/PostgreSQL** - Data persistence
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computations

### Frontend
- **React** or **Vue.js** - UI framework
- **D3.js** or **Chart.js** - Data visualization
- **Material-UI** or **Ant Design** - UI component library
- **Socket.IO Client** - WebSocket communication
- **Axios** - HTTP client for REST API

## Key Design Patterns

### Model-View-Controller (MVC)
- **Model**: SimPy simulation and game state
- **View**: Web UI components and visualizations
- **Controller**: API endpoints and WebSocket handlers

### Observer Pattern
- Simulation entities notify observers of state changes
- Metrics collector subscribes to entity updates
- UI updater receives notifications via WebSocket
- Enables loose coupling between components

### Command Pattern
- Encapsulate user actions as command objects:
  - StartSimulationCommand
  - PauseSimulationCommand
  - PlaceOrderCommand
  - ChangeParameterCommand
- Supports undo/redo functionality
- Enables action logging and replay

### Factory Pattern
- Create supply chain nodes based on configuration
- Generate different scenario types
- Instantiate appropriate policy implementations

## Implementation Flow

### Initialization Phase
1. UI sends configuration parameters via REST API
2. Backend validates configuration
3. SimPy environment created with specified parameters
4. Supply chain entities instantiated
5. WebSocket connection established
6. Initial state pushed to UI

### Simulation Execution
1. Simulation runs in separate thread/process
2. Each simulated week:
   - Process customer demand
   - Execute ordering decisions
   - Process shipments
   - Update inventory levels
   - Calculate costs
3. State updates pushed via WebSocket
4. UI updates visualizations in real-time
5. Metrics logged to database

### User Interaction
1. User inputs received through UI
2. Commands sent via WebSocket
3. Simulation processes commands:
   - Pause/resume simulation clock
   - Apply parameter changes
   - Process manual orders
4. Confirmation sent back to UI
5. UI updates to reflect changes

## State Management Architecture

### Simulation State Structure
```python
{
    "simulation_id": "uuid",
    "current_week": 15,
    "status": "running",  # running, paused, completed
    "nodes": {
        "retailer": {
            "inventory": 12,
            "backlog": 0,
            "pending_orders": [4, 6],
            "last_order": 8,
            "costs": {"holding": 12, "backlog": 0}
        },
        "wholesaler": {
            "inventory": 20,
            "backlog": 2,
            "pending_orders": [8, 10],
            "last_order": 12,
            "costs": {"holding": 20, "backlog": 4}
        },
        "distributor": {...},
        "factory": {...}
    },
    "metrics": {
        "total_cost": 1250,
        "service_level": 0.95,
        "bullwhip_ratio": 2.3
    },
    "orders_in_transit": [
        {"from": "wholesaler", "to": "retailer", "quantity": 6, "arrival_week": 17}
    ]
}
```

### UI State Structure
```javascript
{
    "connection": {
        "status": "connected",
        "latency": 45
    },
    "view": {
        "current": "network",  // network, charts, settings
        "selected_node": "retailer",
        "chart_range": [0, 52]
    },
    "simulation": {
        "status": "running",
        "speed": 1.0,
        "current_week": 15
    },
    "data": {
        "historical": [...],
        "current_state": {...}
    }
}
```

## Scalability Considerations

### Multi-game Support
- Architecture supports multiple simultaneous games
- Each game has unique session ID
- Isolated simulation environments
- Player management and authentication

### Save/Load Functionality
- Serialize complete game state to JSON
- Store in database with timestamp
- Resume simulation from saved state
- Export results for analysis

### Replay System
- Log all events with timestamps
- Store event sequence in database
- Replay capability for:
  - Teaching and demonstrations
  - Performance analysis
  - Debugging

### AI Players
- Pluggable architecture for AI agents
- Support for:
  - Rule-based agents
  - Reinforcement learning agents
  - Predictive models
- Compare human vs AI performance

## Performance Optimization

### Backend Optimization
- Use asyncio for concurrent operations
- Implement caching for frequently accessed data
- Batch WebSocket updates to reduce overhead
- Profile and optimize SimPy event processing

### Frontend Optimization
- Virtual scrolling for large datasets
- Debounce user inputs
- Lazy loading of chart data
- Web workers for heavy computations

## Security Considerations

### Authentication & Authorization
- User authentication for multi-player games
- Role-based access control
- Session management

### Data Validation
- Input sanitization for all user inputs
- Parameter boundary checking
- Rate limiting for API calls

### Communication Security
- HTTPS for all communications
- WSS (WebSocket Secure) for real-time data
- CORS configuration for API access

## Deployment Architecture

### Development Environment
- Docker containers for consistent development
- Hot-reload for both backend and frontend
- Mock data for testing

### Production Environment
- Container orchestration (Docker Compose/Kubernetes)
- Load balancer for multiple backend instances
- CDN for static frontend assets
- Database replication for reliability

## Future Enhancements

### Advanced Features
- Machine learning integration for demand forecasting
- Multi-echelon inventory optimization
- Supply chain disruption scenarios
- Collaborative multi-player mode

### Analytics Dashboard
- Advanced KPI tracking
- Comparative analysis across games
- Learning curve visualization
- Performance benchmarking

### Educational Tools
- Interactive tutorials
- Guided scenarios
- Performance feedback
- Learning assessments

## Conclusion

This architecture provides a robust, scalable foundation for implementing the Beer Distribution Game with modern web technologies. The modular design enables incremental development, starting with core functionality and progressively adding advanced features. The clear separation of concerns ensures maintainability and allows for independent evolution of simulation logic and user interface components.