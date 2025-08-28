"""Core simulation environment management."""

import simpy
import uuid
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from .entities import Retailer, Wholesaler, Distributor, Factory
from .metrics import MetricsCollector


class SimulationStatus(Enum):
    """Simulation status enumeration."""
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""
    
    # Simulation parameters
    weeks: int = 52
    initial_inventory: int = 12
    initial_backlog: int = 0
    
    # Cost parameters
    holding_cost_per_unit: float = 0.5
    backlog_cost_per_unit: float = 1.0
    
    # Lead time parameters
    order_delay: int = 2
    shipment_delay: int = 2
    production_delay: int = 2
    
    # Factory parameters
    production_capacity: int = 100
    
    # Demand pattern
    demand_type: str = "constant"  # constant, step, random, seasonal
    demand_params: Dict[str, Any] = None
    
    # Order policies
    retailer_policy: str = "default"
    wholesaler_policy: str = "default"
    distributor_policy: str = "default"
    factory_policy: str = "default"
    
    def __post_init__(self):
        if self.demand_params is None:
            self.demand_params = {"base_demand": 4}


class SimulationEnvironment:
    """Main simulation environment manager."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize the simulation environment.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.simulation_id = str(uuid.uuid4())
        self.env = simpy.Environment()
        self.status = SimulationStatus.READY
        
        # Supply chain nodes
        self.retailer: Optional[Retailer] = None
        self.wholesaler: Optional[Wholesaler] = None
        self.distributor: Optional[Distributor] = None
        self.factory: Optional[Factory] = None
        self.nodes: List[Any] = []
        
        # Metrics collector
        self.metrics_collector = MetricsCollector(self.simulation_id)
        
        # Event callbacks
        self.on_week_complete: Optional[Callable] = None
        self.on_simulation_complete: Optional[Callable] = None
        
        # Initialize the supply chain
        self._initialize_supply_chain()
    
    def _initialize_supply_chain(self):
        """Initialize the supply chain nodes and connections."""
        
        # Create nodes
        self.retailer = Retailer(
            env=self.env,
            name="Retailer",
            initial_inventory=self.config.initial_inventory,
            initial_backlog=self.config.initial_backlog,
            holding_cost_per_unit=self.config.holding_cost_per_unit,
            backlog_cost_per_unit=self.config.backlog_cost_per_unit,
            order_delay=self.config.order_delay,
            shipment_delay=self.config.shipment_delay,
            demand_pattern=self._create_demand_pattern()
        )
        
        self.wholesaler = Wholesaler(
            env=self.env,
            name="Wholesaler",
            initial_inventory=self.config.initial_inventory,
            initial_backlog=self.config.initial_backlog,
            holding_cost_per_unit=self.config.holding_cost_per_unit,
            backlog_cost_per_unit=self.config.backlog_cost_per_unit,
            order_delay=self.config.order_delay,
            shipment_delay=self.config.shipment_delay
        )
        
        self.distributor = Distributor(
            env=self.env,
            name="Distributor",
            initial_inventory=self.config.initial_inventory,
            initial_backlog=self.config.initial_backlog,
            holding_cost_per_unit=self.config.holding_cost_per_unit,
            backlog_cost_per_unit=self.config.backlog_cost_per_unit,
            order_delay=self.config.order_delay,
            shipment_delay=self.config.shipment_delay
        )
        
        self.factory = Factory(
            env=self.env,
            name="Factory",
            initial_inventory=self.config.initial_inventory,
            initial_backlog=self.config.initial_backlog,
            holding_cost_per_unit=self.config.holding_cost_per_unit,
            backlog_cost_per_unit=self.config.backlog_cost_per_unit,
            production_capacity=self.config.production_capacity,
            production_delay=self.config.production_delay
        )
        
        # Connect nodes in the supply chain
        self.retailer.connect_upstream(self.wholesaler)
        self.wholesaler.connect_upstream(self.distributor)
        self.distributor.connect_upstream(self.factory)
        
        # Store nodes in list for easy iteration
        self.nodes = [self.retailer, self.wholesaler, self.distributor, self.factory]
        
        # Register nodes with metrics collector
        for node in self.nodes:
            self.metrics_collector.register_node(node)
    
    def _create_demand_pattern(self) -> Callable:
        """
        Create a demand pattern function based on configuration.
        
        Returns:
            Function that generates demand for a given week
        """
        demand_type = self.config.demand_type
        params = self.config.demand_params
        
        if demand_type == "constant":
            def demand_pattern(week: int) -> int:
                return params.get("base_demand", 4)
            
        elif demand_type == "step":
            def demand_pattern(week: int) -> int:
                step_week = params.get("step_week", 5)
                base_demand = params.get("base_demand", 4)
                step_demand = params.get("step_demand", 8)
                return step_demand if week >= step_week else base_demand
            
        elif demand_type == "random":
            import random
            def demand_pattern(week: int) -> int:
                base_demand = params.get("base_demand", 4)
                variation = params.get("variation", 2)
                return max(0, base_demand + random.randint(-variation, variation))
            
        elif demand_type == "seasonal":
            import math
            def demand_pattern(week: int) -> int:
                base_demand = params.get("base_demand", 4)
                amplitude = params.get("amplitude", 2)
                period = params.get("period", 52)
                return int(base_demand + amplitude * math.sin(2 * math.pi * week / period))
            
        else:
            # Default to constant demand
            def demand_pattern(week: int) -> int:
                return 4
        
        return demand_pattern
    
    def set_order_policies(
        self,
        retailer_policy: Optional[Callable] = None,
        wholesaler_policy: Optional[Callable] = None,
        distributor_policy: Optional[Callable] = None,
        factory_policy: Optional[Callable] = None
    ):
        """
        Set custom order policies for each node.
        
        Args:
            retailer_policy: Custom ordering policy for retailer
            wholesaler_policy: Custom ordering policy for wholesaler
            distributor_policy: Custom ordering policy for distributor
            factory_policy: Custom production policy for factory
        """
        if retailer_policy and self.retailer:
            self.retailer.order_policy = retailer_policy
        if wholesaler_policy and self.wholesaler:
            self.wholesaler.order_policy = wholesaler_policy
        if distributor_policy and self.distributor:
            self.distributor.order_policy = distributor_policy
        if factory_policy and self.factory:
            self.factory.order_policy = factory_policy
    
    def run(self, weeks: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the simulation.
        
        Args:
            weeks: Number of weeks to simulate (overrides config)
            
        Returns:
            Dictionary containing simulation results
        """
        if self.status != SimulationStatus.READY:
            raise RuntimeError(f"Simulation is not ready to run. Status: {self.status}")
        
        weeks_to_run = weeks or self.config.weeks
        self.status = SimulationStatus.RUNNING
        
        try:
            # Add a process to track progress
            self.env.process(self._monitor_progress(weeks_to_run))
            
            # Run the simulation
            self.env.run(until=weeks_to_run)
            
            # Finalize metrics
            self.metrics_collector.finalize()
            
            self.status = SimulationStatus.COMPLETED
            
            if self.on_simulation_complete:
                self.on_simulation_complete(self.get_results())
            
            return self.get_results()
            
        except Exception as e:
            self.status = SimulationStatus.ERROR
            raise RuntimeError(f"Simulation failed: {str(e)}")
    
    def _monitor_progress(self, total_weeks: int):
        """
        Monitor simulation progress and trigger callbacks.
        
        Args:
            total_weeks: Total number of weeks to simulate
        """
        while self.env.now < total_weeks:
            yield self.env.timeout(1)
            
            # Collect metrics for current week
            self.metrics_collector.collect_current_metrics(int(self.env.now))
            
            # Trigger week complete callback if set
            if self.on_week_complete:
                self.on_week_complete(self.get_current_state())
    
    def pause(self):
        """Pause the simulation (placeholder for future implementation)."""
        if self.status == SimulationStatus.RUNNING:
            self.status = SimulationStatus.PAUSED
    
    def resume(self):
        """Resume the simulation (placeholder for future implementation)."""
        if self.status == SimulationStatus.PAUSED:
            self.status = SimulationStatus.RUNNING
    
    def reset(self):
        """Reset the simulation to initial state."""
        self.__init__(self.config)
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the simulation.
        
        Returns:
            Dictionary containing current simulation state
        """
        return {
            "simulation_id": self.simulation_id,
            "current_week": int(self.env.now),
            "status": self.status.value,
            "nodes": {
                node.name: node.get_state()
                for node in self.nodes
            },
            "metrics": self.metrics_collector.get_summary_statistics()
        }
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get the final simulation results.
        
        Returns:
            Dictionary containing all simulation results
        """
        return {
            "simulation_id": self.simulation_id,
            "status": self.status.value,
            "total_weeks": self.config.weeks,
            "configuration": {
                "initial_inventory": self.config.initial_inventory,
                "holding_cost_per_unit": self.config.holding_cost_per_unit,
                "backlog_cost_per_unit": self.config.backlog_cost_per_unit,
                "order_delay": self.config.order_delay,
                "shipment_delay": self.config.shipment_delay,
                "demand_type": self.config.demand_type
            },
            "summary": self.metrics_collector.get_summary_statistics(),
            "node_summaries": {
                node.name: self.metrics_collector.get_node_summary(node.name)
                for node in self.nodes
            },
            "time_series": self.metrics_collector.metrics.node_histories
        }
    
    def get_time_series_dataframe(self):
        """
        Get time series data as a pandas DataFrame.
        
        Returns:
            DataFrame with all time series data
        """
        return self.metrics_collector.get_time_series_data()
    
    def export_results_json(self) -> Dict[str, Any]:
        """
        Export results in JSON format.
        
        Returns:
            JSON-serializable dictionary of results
        """
        return self.metrics_collector.export_to_json()
