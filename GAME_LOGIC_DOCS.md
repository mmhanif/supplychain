# Beer Distribution Game - Game Logic Layer

## Overview

The game logic layer manages the game rules, player interactions, ordering policies, and scenario configurations for the Beer Distribution Game. It sits on top of the simulation engine layer and provides the gameplay mechanics, win conditions, and strategic elements that make the simulation into an engaging game.

## Architecture Components

### 1. Game Controller (`simulation/game/controller.py`)

The central component that manages game state, rules, and player interactions.

#### Key Features:
- **Game State Management**: Tracks current week, scores, costs, and player decisions
- **Player Management**: Supports human and AI players with different roles
- **Win Conditions**: Configurable targets for cost, service level, and bullwhip effect
- **Game Modes**: Tutorial, collaborative, competitive modes
- **Score Calculation**: Performance-based scoring with leaderboards
- **Decision Handling**: Processes player decisions and updates simulation

#### Classes:
- `GameController`: Main controller class
- `GameStatus`: Enum for game states (SETUP, READY, IN_PROGRESS, PAUSED, COMPLETED)
- `PlayerRole`: Enum for player roles (RETAILER, WHOLESALER, DISTRIBUTOR, FACTORY)
- `Player`: Player representation with score tracking
- `GameRules`: Configurable rules and win conditions
- `GameState`: Complete game state snapshot

### 2. Policy Manager (`simulation/game/policy_manager.py`)

Implements various ordering policies for AI players and decision support.

#### Available Policies:

1. **Base Stock Policy**: Orders up to a target inventory level
2. **EOQ (Economic Order Quantity)**: Minimizes total ordering and holding costs
3. **(s,S) Policy**: Reorder when inventory falls below s, order up to S
4. **Silver-Meal Heuristic**: Dynamic lot-sizing algorithm
5. **Forecast-Based**: Uses demand forecasting with safety stock
6. **Adaptive Policy**: Learns and adjusts based on performance
7. **Custom Policies**: User-defined ordering strategies

#### Features:
- Policy parameter configuration
- Demand forecasting capabilities
- Performance tracking for adaptive learning
- Custom policy registration

### 3. Scenario Manager (`simulation/game/scenario_manager.py`)

Manages predefined and custom game scenarios with different challenges.

#### Predefined Scenarios:

| Scenario | Difficulty | Description | Key Challenge |
|----------|------------|-------------|---------------|
| Classic | Easy | Constant demand of 4 units | Learn basics, avoid bullwhip |
| Demand Surge | Medium | Sudden demand doubling at week 5 | Adapt to step change |
| Seasonal | Medium | Sinusoidal demand pattern | Plan for predictable variation |
| Unpredictable | Hard | Random demand variations | Manage uncertainty |
| Crisis | Hard | Supply chain disruptions | Handle emergencies |
| Growth | Medium | Steadily growing market | Scale operations |
| Volatile | Expert | Extreme fluctuations | Master adaptation |
| Tutorial | Tutorial | Simplified learning scenario | Learn game mechanics |

#### Features:
- Difficulty-based settings (hints, forecasting, time limits)
- Custom scenario creation
- Random scenario generation
- Contextual hints system
- Victory condition customization

## Usage Examples

### Starting a Basic Game

```python
from simulation.game import GameController, GameRules, PlayerRole

# Create game with custom rules
rules = GameRules(
    max_weeks=52,
    target_service_level=0.95,
    collaborative_mode=True
)

# Initialize game controller
game = GameController(game_rules=rules)

# Add players
game.add_player("Alice", PlayerRole.RETAILER, is_human=True)
game.add_player("AI-Bob", PlayerRole.WHOLESALER, is_human=False)

# Start game
game.initialize_game()
game.start_game()

# Submit player decision
game.submit_player_decision(player_id, {"order_quantity": 10})

# Check status
win_status = game.check_win_conditions()
leaderboard = game.get_leaderboard()
```

### Using Policies

```python
from simulation.game import PolicyManager, PolicyType

# Create policy manager
pm = PolicyManager()

# Create a base stock policy
node_context = {
    "inventory": 10,
    "backlog": 2,
    "pending_orders": 5
}

policy = pm.create_policy(
    PolicyType.BASE_STOCK,
    node_context=node_context,
    custom_params={"base_stock_level": 20}
)

# Get order quantity
order_qty = policy(week=5)

# Register custom policy
def aggressive_policy(week):
    return 15 if week < 10 else 10

pm.register_custom_policy("aggressive", aggressive_policy)
```

### Managing Scenarios

```python
from simulation.game import ScenarioManager, DifficultyLevel

# Create scenario manager
sm = ScenarioManager()

# List available scenarios
easy_scenarios = sm.list_scenarios(difficulty=DifficultyLevel.EASY)

# Get specific scenario
scenario = sm.get_scenario("step_change")

# Create simulation config from scenario
config = sm.create_simulation_config("seasonal")

# Create custom scenario
custom_id = sm.create_custom_scenario(
    "My Challenge",
    "Custom supply chain scenario",
    {
        "demand_type": "random",
        "demand_params": {"base_demand": 5, "variation": 2},
        "duration": 40
    }
)

# Generate random scenario
random_id = sm.generate_random_scenario(DifficultyLevel.HARD)
```

## Game Flow

### 1. Setup Phase
```
Create Game Controller → Configure Rules → Add Players → Select Scenario
```

### 2. Initialization
```
Create Simulation → Configure Policies → Set Initial State → Ready to Start
```

### 3. Game Loop
```
For each week:
  Process Demand → Collect Decisions → Execute Orders → 
  Update Inventory → Calculate Costs → Check Win Conditions
```

### 4. Completion
```
Calculate Final Scores → Generate Leaderboard → Save Results
```

## Data Structures

### Game State
```python
{
    "game_id": "uuid",
    "status": "in_progress",
    "current_week": 15,
    "players": {...},
    "total_cost": 5000.0,
    "service_level": 0.92,
    "bullwhip_ratio": 2.1,
    "node_states": {...}
}
```

### Player Decision
```python
{
    "player_id": "uuid",
    "week": 10,
    "order_quantity": 12,
    "timestamp": "2024-01-15T10:30:00"
}
```

### Win Conditions
```python
{
    "all_conditions_met": false,
    "conditions": {
        "cost_target": true,
        "service_target": false,
        "bullwhip_target": true
    },
    "game_complete": false
}
```

## Configuration Options

### Game Rules
- `max_weeks`: Game duration
- `target_service_level`: Required fill rate
- `max_total_cost`: Cost limit for victory
- `enable_information_sharing`: Supply chain visibility
- `enable_forecasting`: Demand prediction
- `cost_penalty_multiplier`: Difficulty adjustment
- `competitive_mode`: Players compete
- `collaborative_mode`: Players cooperate
- `tutorial_mode`: Learning assistance

### Policy Parameters
- `base_stock_level`: Target inventory
- `reorder_point`: (s,S) trigger level
- `order_up_to_level`: (s,S) target level
- `forecast_horizon`: Periods to forecast
- `safety_stock_multiplier`: Buffer sizing
- `learning_rate`: Adaptation speed

### Scenario Settings
- `demand_type`: Pattern of customer demand
- `initial_inventory`: Starting stock levels
- `holding_cost_per_unit`: Inventory carrying cost
- `backlog_cost_per_unit`: Stockout penalty
- `lead_times`: Order and shipment delays
- `disruption_events`: Special challenges

## Performance Metrics

### Cost Metrics
- Total cost (holding + backlog)
- Cost per week
- Cost breakdown by node

### Service Metrics
- Fill rate (% demand satisfied)
- Stockout frequency
- Average backlog

### Efficiency Metrics
- Bullwhip ratio
- Inventory turnover
- Order variability

### Player Metrics
- Score (performance-based)
- Decisions made
- Response time

## Integration with Simulation Engine

The game logic layer integrates seamlessly with the simulation engine:

1. **Scenario → SimulationConfig**: Scenarios generate simulation configurations
2. **Policies → Order Functions**: Policies become ordering functions for nodes
3. **GameController → SimulationEnvironment**: Controller manages simulation lifecycle
4. **Metrics → Scoring**: Simulation metrics feed into scoring system

## Testing

Run the demo to test all components:

```bash
uv run python demo_game_logic.py
```

This demonstrates:
- Game controller with multiple players
- All policy types with examples
- Scenario management and creation
- Integrated gameplay with AI players

## Future Enhancements

### Planned Features
1. **Multiplayer Support**: Real-time collaborative/competitive play
2. **Advanced AI**: Machine learning-based policies
3. **Replay System**: Record and replay games
4. **Tournament Mode**: Multi-game competitions
5. **Analytics Dashboard**: Deep performance analysis
6. **Custom Events**: User-defined disruptions
7. **Team Play**: Multi-role player teams

### API Integration Points
- REST endpoints for game management
- WebSocket for real-time updates
- Event streaming for UI synchronization
- Database persistence for game history

## Dependencies

- `simulation.engine`: Core simulation functionality
- `numpy`: Numerical computations for policies
- `dataclasses`: Data structure definitions
- `enum`: Type-safe enumerations
- `uuid`: Unique identifier generation
- `json`: Game state serialization

## Summary

The game logic layer transforms the beer distribution simulation into an engaging, educational game with:
- Flexible rule configuration
- Multiple difficulty levels and scenarios  
- Sophisticated AI policies
- Comprehensive scoring and win conditions
- Support for both learning and competition

It provides a complete framework for running single or multiplayer beer distribution games with various challenges and objectives.
