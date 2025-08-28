"""Policy Manager for implementing different ordering policies."""

from enum import Enum
from typing import Callable, Dict, Any, Optional, List
import math
import numpy as np
from dataclasses import dataclass


class PolicyType(Enum):
    """Available ordering policy types."""
    MANUAL = "manual"  # Human-controlled
    BASE_STOCK = "base_stock"  # Order up to target level
    EOQ = "eoq"  # Economic Order Quantity
    SILVER_MEAL = "silver_meal"  # Silver-Meal heuristic
    SS_POLICY = "s_S"  # (s,S) inventory policy
    FORECAST_BASED = "forecast_based"  # Based on demand forecast
    ADAPTIVE = "adaptive"  # Adapts based on performance
    CUSTOM = "custom"  # User-defined policy


@dataclass
class PolicyParameters:
    """Parameters for different policies."""
    # Base stock policy
    base_stock_level: int = 20
    
    # EOQ policy
    eoq_quantity: int = 10
    eoq_holding_cost: float = 0.5
    eoq_ordering_cost: float = 10.0
    
    # (s,S) policy
    reorder_point: int = 8  # s
    order_up_to_level: int = 20  # S
    
    # Forecast parameters
    forecast_horizon: int = 4
    safety_stock_multiplier: float = 1.5
    
    # Adaptive parameters
    learning_rate: float = 0.1
    performance_window: int = 10


class PolicyManager:
    """Manages and implements various ordering policies."""
    
    def __init__(self, default_params: Optional[PolicyParameters] = None):
        """
        Initialize the policy manager.
        
        Args:
            default_params: Default parameters for policies
        """
        self.params = default_params or PolicyParameters()
        self.policy_functions: Dict[PolicyType, Callable] = {}
        self.custom_policies: Dict[str, Callable] = {}
        
        # Performance tracking for adaptive policies
        self.performance_history: List[Dict[str, Any]] = []
        self.demand_history: List[float] = []
        
        # Initialize standard policies
        self._initialize_standard_policies()
    
    def _initialize_standard_policies(self):
        """Initialize standard policy functions."""
        self.policy_functions[PolicyType.BASE_STOCK] = self._base_stock_policy
        self.policy_functions[PolicyType.EOQ] = self._eoq_policy
        self.policy_functions[PolicyType.SS_POLICY] = self._ss_policy
        self.policy_functions[PolicyType.SILVER_MEAL] = self._silver_meal_policy
        self.policy_functions[PolicyType.FORECAST_BASED] = self._forecast_based_policy
        self.policy_functions[PolicyType.ADAPTIVE] = self._adaptive_policy
    
    def create_policy(
        self,
        policy_type: PolicyType,
        node_context: Optional[Dict[str, Any]] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Callable[[int], int]:
        """
        Create an ordering policy function.
        
        Args:
            policy_type: Type of policy to create
            node_context: Context about the node (inventory, backlog, etc.)
            custom_params: Custom parameters for the policy
            
        Returns:
            A function that takes week number and returns order quantity
        """
        if policy_type == PolicyType.MANUAL:
            return lambda week: self._manual_policy(week)
        
        if policy_type == PolicyType.CUSTOM:
            if custom_params and "policy_name" in custom_params:
                return self.custom_policies.get(
                    custom_params["policy_name"],
                    lambda week: 4  # Default fallback
                )
        
        # Create a closure that captures the context
        def policy_function(week: int) -> int:
            return self._execute_policy(
                policy_type,
                week,
                node_context or {},
                custom_params or {}
            )
        
        return policy_function
    
    def register_custom_policy(
        self,
        name: str,
        policy_function: Callable[[int], int]
    ):
        """
        Register a custom ordering policy.
        
        Args:
            name: Name of the custom policy
            policy_function: Function implementing the policy
        """
        self.custom_policies[name] = policy_function
    
    def _execute_policy(
        self,
        policy_type: PolicyType,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Execute a specific policy.
        
        Args:
            policy_type: Type of policy to execute
            week: Current week
            node_context: Node state information
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        if policy_type in self.policy_functions:
            return self.policy_functions[policy_type](week, node_context, custom_params)
        return 4  # Default fallback
    
    def _manual_policy(self, week: int) -> int:
        """Manual policy - requires human input."""
        # This would be handled by the game controller
        return 0
    
    def _base_stock_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Base stock policy - order up to target level.
        
        Args:
            week: Current week
            node_context: Node state (inventory, backlog, etc.)
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        target_level = custom_params.get(
            "base_stock_level",
            self.params.base_stock_level
        )
        
        current_inventory = node_context.get("inventory", 0)
        current_backlog = node_context.get("backlog", 0)
        pending_orders = node_context.get("pending_orders", 0)
        
        # Calculate inventory position
        inventory_position = current_inventory - current_backlog + pending_orders
        
        # Order up to target level
        order_quantity = max(0, target_level - inventory_position)
        
        return order_quantity
    
    def _eoq_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Economic Order Quantity policy.
        
        Args:
            week: Current week
            node_context: Node state
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        # Get parameters
        holding_cost = custom_params.get(
            "holding_cost",
            self.params.eoq_holding_cost
        )
        ordering_cost = custom_params.get(
            "ordering_cost",
            self.params.eoq_ordering_cost
        )
        
        # Estimate demand rate
        avg_demand = self._estimate_average_demand()
        
        # Calculate EOQ
        if avg_demand > 0 and holding_cost > 0:
            eoq = math.sqrt((2 * avg_demand * ordering_cost) / holding_cost)
        else:
            eoq = self.params.eoq_quantity
        
        # Check if it's time to order
        current_inventory = node_context.get("inventory", 0)
        reorder_point = avg_demand * 2  # Simple reorder point
        
        if current_inventory <= reorder_point:
            return int(eoq)
        
        return 0
    
    def _ss_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        (s,S) inventory policy.
        
        Args:
            week: Current week
            node_context: Node state
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        s = custom_params.get("reorder_point", self.params.reorder_point)
        S = custom_params.get("order_up_to_level", self.params.order_up_to_level)
        
        current_inventory = node_context.get("inventory", 0)
        current_backlog = node_context.get("backlog", 0)
        pending_orders = node_context.get("pending_orders", 0)
        
        # Calculate inventory position
        inventory_position = current_inventory - current_backlog + pending_orders
        
        # If inventory position <= s, order up to S
        if inventory_position <= s:
            order_quantity = max(0, S - inventory_position)
            return order_quantity
        
        return 0
    
    def _silver_meal_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Silver-Meal heuristic for lot sizing.
        
        Args:
            week: Current week
            node_context: Node state
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        # Get parameters
        holding_cost = custom_params.get(
            "holding_cost",
            self.params.eoq_holding_cost
        )
        ordering_cost = custom_params.get(
            "ordering_cost",
            self.params.eoq_ordering_cost
        )
        
        # Forecast future demands
        forecast = self._forecast_demand(self.params.forecast_horizon)
        
        if not forecast:
            return 4  # Default
        
        # Silver-Meal algorithm
        best_periods = 1
        min_cost_per_period = float('inf')
        
        cumulative_demand = 0
        cumulative_holding_cost = 0
        
        for periods in range(1, min(len(forecast) + 1, 8)):
            if periods <= len(forecast):
                cumulative_demand += forecast[periods - 1]
                
                # Calculate holding cost for this period
                if periods > 1:
                    cumulative_holding_cost += forecast[periods - 1] * (periods - 1) * holding_cost
                
                # Calculate average cost per period
                total_cost = ordering_cost + cumulative_holding_cost
                cost_per_period = total_cost / periods
                
                if cost_per_period < min_cost_per_period:
                    min_cost_per_period = cost_per_period
                    best_periods = periods
        
        # Order for the optimal number of periods
        order_quantity = sum(forecast[:best_periods])
        
        return int(order_quantity)
    
    def _forecast_based_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Policy based on demand forecast.
        
        Args:
            week: Current week
            node_context: Node state
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        # Forecast demand
        forecast_horizon = custom_params.get(
            "forecast_horizon",
            self.params.forecast_horizon
        )
        safety_multiplier = custom_params.get(
            "safety_stock_multiplier",
            self.params.safety_stock_multiplier
        )
        
        # Get forecast
        forecast = self._forecast_demand(forecast_horizon)
        
        if not forecast:
            return 4  # Default
        
        # Calculate expected demand over lead time
        lead_time = node_context.get("lead_time", 2)
        expected_demand = sum(forecast[:lead_time])
        
        # Add safety stock
        demand_std = np.std(self.demand_history) if len(self.demand_history) > 1 else 2
        safety_stock = safety_multiplier * demand_std * math.sqrt(lead_time)
        
        # Calculate target inventory
        target_inventory = expected_demand + safety_stock
        
        # Current position
        current_inventory = node_context.get("inventory", 0)
        current_backlog = node_context.get("backlog", 0)
        pending_orders = node_context.get("pending_orders", 0)
        
        inventory_position = current_inventory - current_backlog + pending_orders
        
        # Order quantity
        order_quantity = max(0, target_inventory - inventory_position)
        
        return int(order_quantity)
    
    def _adaptive_policy(
        self,
        week: int,
        node_context: Dict[str, Any],
        custom_params: Dict[str, Any]
    ) -> int:
        """
        Adaptive policy that learns from performance.
        
        Args:
            week: Current week
            node_context: Node state
            custom_params: Custom parameters
            
        Returns:
            Order quantity
        """
        # Start with base stock policy
        base_quantity = self._base_stock_policy(week, node_context, custom_params)
        
        # Adjust based on recent performance
        if len(self.performance_history) >= self.params.performance_window:
            recent_performance = self.performance_history[-self.params.performance_window:]
            
            # Calculate average service level and cost
            avg_service = np.mean([p.get("service_level", 1.0) for p in recent_performance])
            avg_cost = np.mean([p.get("cost", 0) for p in recent_performance])
            
            # Adjust order quantity based on performance
            if avg_service < 0.95:
                # Increase orders if service level is low
                adjustment = 1.0 + (0.95 - avg_service) * self.params.learning_rate
            else:
                # Slightly decrease if performing well
                adjustment = 1.0 - 0.05 * self.params.learning_rate
            
            base_quantity = int(base_quantity * adjustment)
        
        return base_quantity
    
    def update_demand_history(self, demand: float):
        """
        Update demand history for forecasting.
        
        Args:
            demand: Observed demand
        """
        self.demand_history.append(demand)
        
        # Keep only recent history
        if len(self.demand_history) > 52:
            self.demand_history = self.demand_history[-52:]
    
    def update_performance(self, performance_metrics: Dict[str, Any]):
        """
        Update performance history for adaptive policies.
        
        Args:
            performance_metrics: Dictionary of performance metrics
        """
        self.performance_history.append(performance_metrics)
        
        # Keep only recent history
        if len(self.performance_history) > 52:
            self.performance_history = self.performance_history[-52:]
    
    def _estimate_average_demand(self) -> float:
        """Estimate average demand from history."""
        if self.demand_history:
            return np.mean(self.demand_history)
        return 4.0  # Default
    
    def _forecast_demand(self, horizon: int) -> List[float]:
        """
        Forecast future demand.
        
        Args:
            horizon: Number of periods to forecast
            
        Returns:
            List of forecasted demands
        """
        if len(self.demand_history) < 4:
            # Not enough history, use simple average
            avg_demand = self._estimate_average_demand()
            return [avg_demand] * horizon
        
        # Simple moving average forecast
        window_size = min(4, len(self.demand_history))
        recent_demands = self.demand_history[-window_size:]
        avg_demand = np.mean(recent_demands)
        
        # Add some trend analysis
        if len(self.demand_history) >= 8:
            older_avg = np.mean(self.demand_history[-8:-4])
            trend = (avg_demand - older_avg) / 4
        else:
            trend = 0
        
        # Generate forecast
        forecast = []
        for i in range(horizon):
            forecast.append(max(0, avg_demand + trend * i))
        
        return forecast
    
    def get_policy_info(self, policy_type: PolicyType) -> Dict[str, Any]:
        """
        Get information about a policy.
        
        Args:
            policy_type: Type of policy
            
        Returns:
            Dictionary with policy information
        """
        info = {
            "name": policy_type.value,
            "description": "",
            "parameters": {}
        }
        
        if policy_type == PolicyType.BASE_STOCK:
            info["description"] = "Orders up to a target inventory level"
            info["parameters"] = {
                "base_stock_level": self.params.base_stock_level
            }
        elif policy_type == PolicyType.EOQ:
            info["description"] = "Economic Order Quantity - minimizes total cost"
            info["parameters"] = {
                "eoq_quantity": self.params.eoq_quantity,
                "holding_cost": self.params.eoq_holding_cost,
                "ordering_cost": self.params.eoq_ordering_cost
            }
        elif policy_type == PolicyType.SS_POLICY:
            info["description"] = "(s,S) policy - order up to S when inventory falls below s"
            info["parameters"] = {
                "reorder_point": self.params.reorder_point,
                "order_up_to_level": self.params.order_up_to_level
            }
        elif policy_type == PolicyType.FORECAST_BASED:
            info["description"] = "Orders based on demand forecast and safety stock"
            info["parameters"] = {
                "forecast_horizon": self.params.forecast_horizon,
                "safety_stock_multiplier": self.params.safety_stock_multiplier
            }
        elif policy_type == PolicyType.ADAPTIVE:
            info["description"] = "Adapts ordering based on recent performance"
            info["parameters"] = {
                "learning_rate": self.params.learning_rate,
                "performance_window": self.params.performance_window
            }
        
        return info
