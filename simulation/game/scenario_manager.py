"""Scenario Manager for handling different game scenarios and configurations."""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import random
import math

from ..engine.core import SimulationConfig


class ScenarioType(Enum):
    """Types of predefined scenarios."""
    CLASSIC = "classic"  # Original beer game setup
    STEP_DEMAND = "step_demand"  # Sudden demand change
    SEASONAL = "seasonal"  # Seasonal demand pattern
    RANDOM_WALK = "random_walk"  # Random demand variations
    DISRUPTION = "disruption"  # Supply chain disruption
    GROWTH = "growth"  # Growing demand
    VOLATILE = "volatile"  # High volatility
    CUSTOM = "custom"  # User-defined scenario


class DifficultyLevel(Enum):
    """Difficulty levels for scenarios."""
    TUTORIAL = "tutorial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class ScenarioDefinition:
    """Defines a complete scenario."""
    name: str
    description: str
    type: ScenarioType
    difficulty: DifficultyLevel
    
    # Demand configuration
    demand_type: str
    demand_params: Dict[str, Any]
    
    # Initial conditions
    initial_inventory: int = 12
    initial_backlog: int = 0
    
    # Cost parameters
    holding_cost_per_unit: float = 0.5
    backlog_cost_per_unit: float = 1.0
    
    # Lead times
    order_delay: int = 2
    shipment_delay: int = 2
    production_delay: int = 2
    
    # Constraints
    production_capacity: int = 100
    max_order_quantity: Optional[int] = None
    min_order_quantity: int = 0
    
    # Special events
    disruption_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Victory conditions
    target_cost: Optional[float] = None
    target_service_level: float = 0.95
    max_bullwhip_ratio: float = 3.0
    
    # Duration
    duration_weeks: int = 52
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)


class ScenarioManager:
    """Manages game scenarios and configurations."""
    
    def __init__(self):
        """Initialize the scenario manager."""
        self.scenarios: Dict[str, ScenarioDefinition] = {}
        self.custom_scenarios: Dict[str, ScenarioDefinition] = {}
        
        # Initialize predefined scenarios
        self._initialize_predefined_scenarios()
    
    def _initialize_predefined_scenarios(self):
        """Initialize all predefined scenarios."""
        
        # Classic Beer Game
        self.scenarios["classic"] = ScenarioDefinition(
            name="Classic Beer Game",
            description="The original beer distribution game with constant demand",
            type=ScenarioType.CLASSIC,
            difficulty=DifficultyLevel.EASY,
            demand_type="constant",
            demand_params={"base_demand": 4},
            duration_weeks=52,
            tags=["classic", "beginner", "constant"],
            hints=[
                "Demand is constant at 4 units per week",
                "Watch out for the bullwhip effect",
                "Order consistently to avoid stockouts"
            ]
        )
        
        # Step Demand Change
        self.scenarios["step_change"] = ScenarioDefinition(
            name="Demand Surge",
            description="Sudden increase in demand after initial stability",
            type=ScenarioType.STEP_DEMAND,
            difficulty=DifficultyLevel.MEDIUM,
            demand_type="step",
            demand_params={
                "base_demand": 4,
                "step_demand": 8,
                "step_week": 5
            },
            duration_weeks=52,
            target_service_level=0.90,
            tags=["step", "intermediate", "surprise"],
            hints=[
                "Demand will double at week 5",
                "Build safety stock before the surge",
                "Coordinate with other players"
            ]
        )
        
        # Seasonal Pattern
        self.scenarios["seasonal"] = ScenarioDefinition(
            name="Seasonal Demand",
            description="Demand follows a seasonal pattern throughout the year",
            type=ScenarioType.SEASONAL,
            difficulty=DifficultyLevel.MEDIUM,
            demand_type="seasonal",
            demand_params={
                "base_demand": 6,
                "amplitude": 3,
                "period": 52
            },
            duration_weeks=52,
            tags=["seasonal", "predictable", "planning"],
            hints=[
                "Demand peaks in the middle of the year",
                "Plan inventory for peak season",
                "Use forecasting to anticipate changes"
            ]
        )
        
        # Random Walk
        self.scenarios["random_walk"] = ScenarioDefinition(
            name="Unpredictable Market",
            description="Demand varies randomly each week",
            type=ScenarioType.RANDOM_WALK,
            difficulty=DifficultyLevel.HARD,
            demand_type="random",
            demand_params={
                "base_demand": 5,
                "variation": 3
            },
            duration_weeks=52,
            target_service_level=0.85,
            tags=["random", "challenging", "adaptive"],
            hints=[
                "Demand varies between 2 and 8 units",
                "Maintain safety stock",
                "React quickly to changes"
            ]
        )
        
        # Supply Chain Disruption
        self.scenarios["disruption"] = ScenarioDefinition(
            name="Crisis Management",
            description="Handle supply chain disruptions and recovery",
            type=ScenarioType.DISRUPTION,
            difficulty=DifficultyLevel.HARD,
            demand_type="constant",
            demand_params={"base_demand": 5},
            duration_weeks=52,
            disruption_events=[
                {
                    "week": 15,
                    "type": "factory_shutdown",
                    "duration": 3,
                    "description": "Factory maintenance shutdown"
                },
                {
                    "week": 30,
                    "type": "demand_spike",
                    "multiplier": 3,
                    "duration": 2,
                    "description": "Promotional campaign causes demand spike"
                }
            ],
            tags=["disruption", "crisis", "advanced"],
            hints=[
                "Build inventory before week 15",
                "Factory will be offline for 3 weeks",
                "Expect demand spike at week 30"
            ]
        )
        
        # Growth Scenario
        self.scenarios["growth"] = ScenarioDefinition(
            name="Market Growth",
            description="Manage supply chain during market expansion",
            type=ScenarioType.GROWTH,
            difficulty=DifficultyLevel.MEDIUM,
            demand_type="growth",
            demand_params={
                "initial_demand": 3,
                "growth_rate": 0.02,
                "max_demand": 12
            },
            duration_weeks=52,
            production_capacity=150,
            tags=["growth", "expansion", "strategic"],
            hints=[
                "Demand grows by 2% weekly",
                "Plan capacity for future demand",
                "Balance growth with costs"
            ]
        )
        
        # High Volatility
        self.scenarios["volatile"] = ScenarioDefinition(
            name="Volatile Market",
            description="Extreme demand fluctuations test your adaptability",
            type=ScenarioType.VOLATILE,
            difficulty=DifficultyLevel.EXPERT,
            demand_type="volatile",
            demand_params={
                "base_demand": 6,
                "volatility": 0.5,
                "shock_probability": 0.1
            },
            duration_weeks=52,
            holding_cost_per_unit=0.3,
            backlog_cost_per_unit=2.0,
            target_service_level=0.80,
            tags=["volatile", "expert", "challenging"],
            hints=[
                "Expect sudden demand shocks",
                "Balance inventory vs stockout risks",
                "Use adaptive strategies"
            ]
        )
        
        # Tutorial Scenario
        self.scenarios["tutorial"] = ScenarioDefinition(
            name="Tutorial",
            description="Learn the basics of the beer game",
            type=ScenarioType.CLASSIC,
            difficulty=DifficultyLevel.TUTORIAL,
            demand_type="constant",
            demand_params={"base_demand": 4},
            duration_weeks=20,
            initial_inventory=20,
            holding_cost_per_unit=0.25,
            backlog_cost_per_unit=0.5,
            tags=["tutorial", "learning", "simple"],
            hints=[
                "Try to match your orders to demand",
                "Keep some safety stock",
                "Watch your costs"
            ]
        )
    
    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDefinition]:
        """
        Get a scenario by ID.
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            ScenarioDefinition or None if not found
        """
        # Check predefined scenarios first
        if scenario_id in self.scenarios:
            return self.scenarios[scenario_id]
        
        # Then check custom scenarios
        if scenario_id in self.custom_scenarios:
            return self.custom_scenarios[scenario_id]
        
        return None
    
    def list_scenarios(
        self,
        difficulty: Optional[DifficultyLevel] = None,
        scenario_type: Optional[ScenarioType] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List available scenarios with optional filters.
        
        Args:
            difficulty: Filter by difficulty level
            scenario_type: Filter by scenario type
            tags: Filter by tags
            
        Returns:
            List of scenario summaries
        """
        scenarios_list = []
        
        # Combine predefined and custom scenarios
        all_scenarios = {**self.scenarios, **self.custom_scenarios}
        
        for scenario_id, scenario in all_scenarios.items():
            # Apply filters
            if difficulty and scenario.difficulty != difficulty:
                continue
            
            if scenario_type and scenario.type != scenario_type:
                continue
            
            if tags:
                if not any(tag in scenario.tags for tag in tags):
                    continue
            
            # Create summary
            scenarios_list.append({
                "id": scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "type": scenario.type.value,
                "difficulty": scenario.difficulty.value,
                "duration": scenario.duration_weeks,
                "tags": scenario.tags
            })
        
        return scenarios_list
    
    def create_simulation_config(
        self,
        scenario_id: str
    ) -> SimulationConfig:
        """
        Create a simulation configuration from a scenario.
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            SimulationConfig for the scenario
        """
        scenario = self.get_scenario(scenario_id)
        
        if not scenario:
            # Return default config if scenario not found
            return SimulationConfig()
        
        # Map scenario demand type to simulation demand type
        demand_type = scenario.demand_type
        demand_params = scenario.demand_params.copy()
        
        # Handle special demand types
        if demand_type == "growth":
            # Convert growth to custom function
            demand_type = "custom"
            initial = demand_params.get("initial_demand", 3)
            rate = demand_params.get("growth_rate", 0.02)
            max_demand = demand_params.get("max_demand", 12)
            
            demand_params = {
                "function": lambda week: min(
                    max_demand,
                    int(initial * (1 + rate) ** week)
                )
            }
        
        elif demand_type == "volatile":
            # Convert volatile to random with shocks
            demand_type = "random"
            base = demand_params.get("base_demand", 6)
            volatility = demand_params.get("volatility", 0.5)
            
            demand_params = {
                "base_demand": base,
                "variation": int(base * volatility)
            }
        
        # Create simulation config
        config = SimulationConfig(
            weeks=scenario.duration_weeks,
            initial_inventory=scenario.initial_inventory,
            initial_backlog=scenario.initial_backlog,
            holding_cost_per_unit=scenario.holding_cost_per_unit,
            backlog_cost_per_unit=scenario.backlog_cost_per_unit,
            order_delay=scenario.order_delay,
            shipment_delay=scenario.shipment_delay,
            production_delay=scenario.production_delay,
            production_capacity=scenario.production_capacity,
            demand_type=demand_type,
            demand_params=demand_params
        )
        
        return config
    
    def create_custom_scenario(
        self,
        name: str,
        description: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Create a custom scenario.
        
        Args:
            name: Name of the scenario
            description: Description of the scenario
            config: Configuration dictionary
            
        Returns:
            ID of the created scenario
        """
        # Generate unique ID
        scenario_id = f"custom_{len(self.custom_scenarios)}_{name.lower().replace(' ', '_')}"
        
        # Create scenario definition
        scenario = ScenarioDefinition(
            name=name,
            description=description,
            type=ScenarioType.CUSTOM,
            difficulty=DifficultyLevel(config.get("difficulty", "medium")),
            demand_type=config.get("demand_type", "constant"),
            demand_params=config.get("demand_params", {"base_demand": 4}),
            initial_inventory=config.get("initial_inventory", 12),
            initial_backlog=config.get("initial_backlog", 0),
            holding_cost_per_unit=config.get("holding_cost", 0.5),
            backlog_cost_per_unit=config.get("backlog_cost", 1.0),
            duration_weeks=config.get("duration", 52),
            tags=config.get("tags", ["custom"])
        )
        
        # Store custom scenario
        self.custom_scenarios[scenario_id] = scenario
        
        return scenario_id
    
    def get_scenario_hints(
        self,
        scenario_id: str,
        week: int
    ) -> List[str]:
        """
        Get contextual hints for a scenario.
        
        Args:
            scenario_id: ID of the scenario
            week: Current week
            
        Returns:
            List of relevant hints
        """
        scenario = self.get_scenario(scenario_id)
        
        if not scenario:
            return []
        
        hints = []
        
        # Add general hints
        if week <= 5:
            hints.extend(scenario.hints[:1])  # Early game hints
        
        # Add event-specific hints
        for event in scenario.disruption_events:
            event_week = event.get("week", 0)
            if week == event_week - 2:
                hints.append(f"Prepare for: {event.get('description', 'upcoming event')}")
            elif week == event_week:
                hints.append(f"Event active: {event.get('description', 'special event')}")
        
        # Add performance-based hints
        if week > 10:
            hints.append("Review your performance metrics")
        
        return hints
    
    def get_difficulty_settings(
        self,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """
        Get game settings based on difficulty level.
        
        Args:
            difficulty: Difficulty level
            
        Returns:
            Dictionary of difficulty-specific settings
        """
        settings = {
            DifficultyLevel.TUTORIAL: {
                "hints_enabled": True,
                "forecast_enabled": True,
                "information_sharing": True,
                "cost_multiplier": 0.5,
                "time_limit": None
            },
            DifficultyLevel.EASY: {
                "hints_enabled": True,
                "forecast_enabled": True,
                "information_sharing": False,
                "cost_multiplier": 0.75,
                "time_limit": None
            },
            DifficultyLevel.MEDIUM: {
                "hints_enabled": False,
                "forecast_enabled": True,
                "information_sharing": False,
                "cost_multiplier": 1.0,
                "time_limit": 120  # seconds per decision
            },
            DifficultyLevel.HARD: {
                "hints_enabled": False,
                "forecast_enabled": False,
                "information_sharing": False,
                "cost_multiplier": 1.25,
                "time_limit": 60
            },
            DifficultyLevel.EXPERT: {
                "hints_enabled": False,
                "forecast_enabled": False,
                "information_sharing": False,
                "cost_multiplier": 1.5,
                "time_limit": 30
            }
        }
        
        return settings.get(difficulty, settings[DifficultyLevel.MEDIUM])
    
    def generate_random_scenario(
        self,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> str:
        """
        Generate a random scenario based on difficulty.
        
        Args:
            difficulty: Target difficulty level
            
        Returns:
            ID of the generated scenario
        """
        # Random parameters based on difficulty
        if difficulty == DifficultyLevel.EASY:
            demand_types = ["constant", "step"]
            cost_range = (0.25, 0.5)
            duration = random.choice([26, 39, 52])
        elif difficulty == DifficultyLevel.HARD:
            demand_types = ["random", "seasonal", "volatile"]
            cost_range = (0.5, 1.5)
            duration = 52
        else:  # Medium
            demand_types = ["step", "seasonal", "random"]
            cost_range = (0.4, 0.8)
            duration = random.choice([39, 52])
        
        # Generate random configuration
        demand_type = random.choice(demand_types)
        
        config = {
            "difficulty": difficulty.value,
            "demand_type": demand_type,
            "demand_params": self._generate_demand_params(demand_type),
            "holding_cost": random.uniform(*cost_range),
            "backlog_cost": random.uniform(cost_range[1], cost_range[1] * 3),
            "duration": duration,
            "initial_inventory": random.randint(8, 20),
            "tags": ["random", "generated", difficulty.value]
        }
        
        # Create scenario
        name = f"Random Challenge #{random.randint(1000, 9999)}"
        description = f"A randomly generated {difficulty.value} scenario"
        
        return self.create_custom_scenario(name, description, config)
    
    def _generate_demand_params(self, demand_type: str) -> Dict[str, Any]:
        """Generate random demand parameters for a given type."""
        if demand_type == "constant":
            return {"base_demand": random.randint(3, 7)}
        elif demand_type == "step":
            return {
                "base_demand": random.randint(3, 5),
                "step_demand": random.randint(6, 10),
                "step_week": random.randint(5, 15)
            }
        elif demand_type == "seasonal":
            return {
                "base_demand": random.randint(4, 8),
                "amplitude": random.randint(2, 4),
                "period": random.choice([26, 52])
            }
        elif demand_type == "random":
            base = random.randint(4, 7)
            return {
                "base_demand": base,
                "variation": random.randint(1, base // 2)
            }
        else:
            return {"base_demand": 5}
