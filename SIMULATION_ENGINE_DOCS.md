# Beer Distribution Game Simulation Engine

## Overview

This is the Python implementation of the simulation engine layer for the Beer Distribution Game, as specified in `beer_game_architecture.md`. The engine uses SimPy for discrete event simulation and provides a complete framework for modeling supply chain dynamics.

## Architecture

The simulation engine is organized into the following components:

### Core Components

1. **SimulationEnvironment** (`simulation/engine/core.py`)
   - Main orchestrator for the simulation
   - Manages SimPy environment and simulation lifecycle
   - Handles configuration and state management
   - Provides callbacks for real-time monitoring

2. **Supply Chain Entities** (`simulation/engine/entities/`)
   - **SupplyChainNode** (base.py): Abstract base class for all nodes
   - **Retailer** (nodes.py): Faces external customer demand
   - **Wholesaler** (nodes.py): Intermediate node
   - **Distributor** (nodes.py): Intermediate node  
   - **Factory** (nodes.py): Produces goods with production delay

3. **Order/Inventory Management** (`simulation/engine/entities/base.py`)
   - Order processing and fulfillment logic
   - Backlog management
   - Shipment tracking
   - Lead time handling

4. **Metrics Collection** (`simulation/engine/metrics.py`)
   - Real-time KPI tracking
   - Time-series data collection
   - Bullwhip effect calculation
   - Service level metrics
   - Cost analysis

## Features

### Implemented Features

✅ **Discrete Event Simulation**
- SimPy-based event scheduling
- Week-by-week simulation progression
- Proper lead time modeling

✅ **Supply Chain Modeling**
- Four-tier supply chain (Retailer → Wholesaler → Distributor → Factory)
- Order delays and shipment delays
- Inventory and backlog tracking
- Production delays for factory

✅ **Demand Patterns**
- Constant demand
- Step change demand
- Random variation
- Seasonal patterns

✅ **Cost Calculation**
- Holding costs
- Backlog/stockout penalties
- Total supply chain costs

✅ **Performance Metrics**
- Fill rate calculation
- Service levels
- Bullwhip effect measurement
- Node-specific and system-wide metrics

✅ **Flexible Configuration**
- Configurable initial conditions
- Adjustable cost parameters
- Customizable lead times
- Different ordering policies

## Usage

### Basic Example

```python
from simulation.engine import SimulationEnvironment
from simulation.engine.core import SimulationConfig

# Create configuration
config = SimulationConfig(
    weeks=52,
    initial_inventory=12,
    holding_cost_per_unit=0.5,
    backlog_cost_per_unit=1.0,
    demand_type="constant",
    demand_params={"base_demand": 4}
)

# Run simulation
sim = SimulationEnvironment(config)
results = sim.run()

# Access results
print(f"Total Cost: ${results['summary']['total_cost']:.2f}")
print(f"Fill Rate: {results['summary']['fill_rate']:.2%}")
print(f"Bullwhip Ratio: {results['summary']['bullwhip_ratio']:.2f}")
```

### Advanced Configuration

```python
# Step demand scenario
config = SimulationConfig(
    weeks=52,
    demand_type="step",
    demand_params={
        "base_demand": 4,
        "step_demand": 8,
        "step_week": 5
    }
)

# Custom callbacks for monitoring
sim = SimulationEnvironment(config)
sim.on_week_complete = lambda state: print(f"Week {state['current_week']}")
results = sim.run()
```

### Custom Order Policies

```python
def custom_retailer_policy(week: int) -> int:
    """Example custom ordering policy"""
    if week < 10:
        return 4
    else:
        return 8

sim.set_order_policies(retailer_policy=custom_retailer_policy)
```

## Data Structures

### Simulation State
```python
{
    "simulation_id": "uuid",
    "current_week": 15,
    "status": "running",
    "nodes": {
        "Retailer": {...},
        "Wholesaler": {...},
        "Distributor": {...},
        "Factory": {...}
    },
    "metrics": {...}
}
```

### Node State
```python
{
    "name": "Retailer",
    "type": "retailer",
    "inventory": 12,
    "backlog": 0,
    "pending_orders": 2,
    "incoming_shipments": 1,
    "last_order": 4,
    "costs": {
        "holding_cost": 6.0,
        "backlog_cost": 0.0,
        "total_cost": 6.0
    }
}
```

## Testing

Run the demo script to test the simulation engine:

```bash
uv run python demo_simulation.py
```

This will:
1. Run multiple scenarios (constant, step, random demand)
2. Compare results across scenarios
3. Save results to `simulation_results.json`
4. Display performance metrics

## Dependencies

- Python 3.10+
- SimPy 4.1.1+ (discrete event simulation)
- NumPy 2.2.6+ (numerical computations)
- Pandas 2.3.2+ (data analysis)

## Future Enhancements

The current implementation provides the foundation for:

1. **Web Interface Integration**
   - REST API endpoints
   - WebSocket support for real-time updates
   - Event streaming

2. **Advanced Policies**
   - Base-stock policies
   - (s,S) inventory policies
   - Machine learning-based policies

3. **Multiplayer Support**
   - Multiple simultaneous games
   - Player authentication
   - Game state persistence

4. **Analytics Dashboard**
   - Advanced visualizations
   - Comparative analysis
   - Learning curve tracking

## File Structure

```
simulation/
├── __init__.py
└── engine/
    ├── __init__.py
    ├── core.py              # Main simulation environment
    ├── metrics.py           # Metrics collection system
    └── entities/
        ├── __init__.py
        ├── base.py          # Base classes and abstractions
        └── nodes.py         # Specific node implementations
```

## Design Patterns Used

1. **Abstract Factory**: Node creation based on configuration
2. **Observer**: Metrics collection subscribes to node updates
3. **Template Method**: Base node class defines simulation loop
4. **Strategy**: Configurable ordering policies and demand patterns

## Notes

- The simulation uses discrete time steps (weeks)
- All nodes process simultaneously each week
- Order and shipment delays are properly modeled
- The factory has unlimited raw materials but production delay
- Metrics are collected every simulation week

This implementation follows the architecture outlined in `beer_game_architecture.md` and provides a solid foundation for the complete Beer Distribution Game system.
