"""Specific supply chain node implementations."""

from typing import Optional, Callable
import simpy
import random
from .base import SupplyChainNode, NodeType, Order


class Retailer(SupplyChainNode):
    """Retailer node - faces external customer demand."""
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str = "Retailer",
        initial_inventory: int = 12,
        initial_backlog: int = 0,
        holding_cost_per_unit: float = 0.5,
        backlog_cost_per_unit: float = 1.0,
        order_delay: int = 2,
        shipment_delay: int = 2,
        order_policy: Optional[Callable] = None,
        demand_pattern: Optional[Callable] = None
    ):
        """
        Initialize a Retailer node.
        
        Args:
            env: SimPy environment
            name: Name of the retailer
            initial_inventory: Starting inventory level
            initial_backlog: Starting backlog amount
            holding_cost_per_unit: Cost per unit of inventory held per week
            backlog_cost_per_unit: Cost per unit of backlog per week
            order_policy: Function to determine order quantity
            demand_pattern: Function to generate customer demand
        """
        super().__init__(
            env=env,
            name=name,
            node_type=NodeType.RETAILER,
            initial_inventory=initial_inventory,
            initial_backlog=initial_backlog,
            holding_cost_per_unit=holding_cost_per_unit,
            backlog_cost_per_unit=backlog_cost_per_unit,
            order_delay=order_delay,
            shipment_delay=shipment_delay
        )
        
        self.order_policy = order_policy or self.default_order_policy
        self.demand_pattern = demand_pattern or self.default_demand_pattern
        self.customer_demands = []
    
    def default_order_policy(self, week: int) -> int:
        """Default ordering policy - order same as demand."""
        if self.customer_demands:
            return self.customer_demands[-1]
        return 4  # Default order quantity
    
    def default_demand_pattern(self, week: int) -> int:
        """Default demand pattern - constant demand of 4 units."""
        return 4
    
    def get_order_quantity(self, week: int) -> int:
        """Determine order quantity using the configured policy."""
        return self.order_policy(week)
    
    def process_customer_demand(self, week: int):
        """Process external customer demand."""
        demand = self.demand_pattern(week)
        self.customer_demands.append(demand)
        
        # Create a customer order
        customer_order = Order(
            quantity=demand,
            week_placed=week,
            from_node="customer",
            to_node=self.name
        )
        
        # Process the order immediately (customer orders have no delay)
        self.receive_order(customer_order)
    
    def run(self):
        """Main process loop for the retailer."""
        while True:
            current_week = int(self.env.now)
            
            # First process customer demand
            self.process_customer_demand(current_week)
            
            # Then run the standard node process
            # Process incoming shipments that have arrived
            arrived_shipments = [
                s for s in self.incoming_shipments 
                if s.week_to_arrive == current_week
            ]
            for shipment in arrived_shipments:
                self.receive_shipment(shipment)
                self.incoming_shipments.remove(shipment)
            
            # Determine order quantity and place order to upstream
            order_quantity = self.get_order_quantity(current_week)
            if order_quantity > 0:
                self.place_order(order_quantity)
            
            # Record metrics for this period
            self.record_metrics()
            
            # Wait for next period
            yield self.env.timeout(1)


class Wholesaler(SupplyChainNode):
    """Wholesaler node - intermediate node in the supply chain."""
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str = "Wholesaler",
        initial_inventory: int = 12,
        initial_backlog: int = 0,
        holding_cost_per_unit: float = 0.5,
        backlog_cost_per_unit: float = 1.0,
        order_delay: int = 2,
        shipment_delay: int = 2,
        order_policy: Optional[Callable] = None
    ):
        """Initialize a Wholesaler node."""
        super().__init__(
            env=env,
            name=name,
            node_type=NodeType.WHOLESALER,
            initial_inventory=initial_inventory,
            initial_backlog=initial_backlog,
            holding_cost_per_unit=holding_cost_per_unit,
            backlog_cost_per_unit=backlog_cost_per_unit,
            order_delay=order_delay,
            shipment_delay=shipment_delay
        )
        
        self.order_policy = order_policy or self.default_order_policy
    
    def default_order_policy(self, week: int) -> int:
        """Default ordering policy - match incoming orders."""
        if self.orders_received:
            recent_orders = [o for o in self.orders_received if o.week_placed >= week - 1]
            if recent_orders:
                return recent_orders[-1].quantity
        return 4  # Default order quantity
    
    def get_order_quantity(self, week: int) -> int:
        """Determine order quantity using the configured policy."""
        return self.order_policy(week)


class Distributor(SupplyChainNode):
    """Distributor node - intermediate node in the supply chain."""
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str = "Distributor",
        initial_inventory: int = 12,
        initial_backlog: int = 0,
        holding_cost_per_unit: float = 0.5,
        backlog_cost_per_unit: float = 1.0,
        order_delay: int = 2,
        shipment_delay: int = 2,
        order_policy: Optional[Callable] = None
    ):
        """Initialize a Distributor node."""
        super().__init__(
            env=env,
            name=name,
            node_type=NodeType.DISTRIBUTOR,
            initial_inventory=initial_inventory,
            initial_backlog=initial_backlog,
            holding_cost_per_unit=holding_cost_per_unit,
            backlog_cost_per_unit=backlog_cost_per_unit,
            order_delay=order_delay,
            shipment_delay=shipment_delay
        )
        
        self.order_policy = order_policy or self.default_order_policy
    
    def default_order_policy(self, week: int) -> int:
        """Default ordering policy - match incoming orders."""
        if self.orders_received:
            recent_orders = [o for o in self.orders_received if o.week_placed >= week - 1]
            if recent_orders:
                return recent_orders[-1].quantity
        return 4  # Default order quantity
    
    def get_order_quantity(self, week: int) -> int:
        """Determine order quantity using the configured policy."""
        return self.order_policy(week)


class Factory(SupplyChainNode):
    """Factory node - produces goods with unlimited raw materials."""
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str = "Factory",
        initial_inventory: int = 12,
        initial_backlog: int = 0,
        holding_cost_per_unit: float = 0.5,
        backlog_cost_per_unit: float = 1.0,
        production_capacity: int = 100,
        production_delay: int = 2,
        order_policy: Optional[Callable] = None
    ):
        """
        Initialize a Factory node.
        
        Args:
            env: SimPy environment
            name: Name of the factory
            initial_inventory: Starting inventory level
            initial_backlog: Starting backlog amount
            holding_cost_per_unit: Cost per unit of inventory held per week
            backlog_cost_per_unit: Cost per unit of backlog per week
            production_capacity: Maximum production per week
            production_delay: Delay in weeks for production
            order_policy: Function to determine production quantity
        """
        super().__init__(
            env=env,
            name=name,
            node_type=NodeType.FACTORY,
            initial_inventory=initial_inventory,
            initial_backlog=initial_backlog,
            holding_cost_per_unit=holding_cost_per_unit,
            backlog_cost_per_unit=backlog_cost_per_unit
        )
        
        self.production_capacity = production_capacity
        self.production_delay = production_delay
        self.order_policy = order_policy or self.default_order_policy
        self.production_queue = []
    
    def default_order_policy(self, week: int) -> int:
        """Default production policy - match incoming orders."""
        if self.orders_received:
            recent_orders = [o for o in self.orders_received if o.week_placed >= week - 1]
            if recent_orders:
                return min(recent_orders[-1].quantity, self.production_capacity)
        return 4  # Default production quantity
    
    def get_order_quantity(self, week: int) -> int:
        """
        For factory, this determines production quantity.
        No upstream orders are placed as factory has unlimited raw materials.
        """
        return self.order_policy(week)
    
    def place_order(self, quantity: int):
        """
        Override place_order to schedule production instead of ordering.
        
        Args:
            quantity: Number of units to produce
        """
        # Schedule production to complete after production delay
        production_complete_week = int(self.env.now) + self.production_delay
        self.production_queue.append({
            'quantity': min(quantity, self.production_capacity),
            'complete_week': production_complete_week
        })
    
    def run(self):
        """Main process loop for the factory."""
        while True:
            current_week = int(self.env.now)
            
            # Process completed production
            completed_production = [
                p for p in self.production_queue 
                if p['complete_week'] == current_week
            ]
            for production in completed_production:
                self.inventory += production['quantity']
                self.production_queue.remove(production)
            
            # Process pending orders that have arrived
            arrived_orders = [
                o for o in self.pending_orders 
                if o.week_to_arrive == current_week
            ]
            for order in arrived_orders:
                self.receive_order(order)
                self.pending_orders.remove(order)
            
            # Determine production quantity and schedule production
            production_quantity = self.get_order_quantity(current_week)
            if production_quantity > 0:
                self.place_order(production_quantity)  # This schedules production
            
            # Record metrics for this period
            self.record_metrics()
            
            # Wait for next period
            yield self.env.timeout(1)
