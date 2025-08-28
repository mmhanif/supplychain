"""Base class for supply chain entities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import simpy
from enum import Enum


class NodeType(Enum):
    """Enumeration of supply chain node types."""
    RETAILER = "retailer"
    WHOLESALER = "wholesaler"
    DISTRIBUTOR = "distributor"
    FACTORY = "factory"


@dataclass
class Order:
    """Represents an order in the supply chain."""
    quantity: int
    week_placed: int
    from_node: Optional[str] = None
    to_node: Optional[str] = None
    week_to_arrive: Optional[int] = None


@dataclass
class Shipment:
    """Represents a shipment between nodes."""
    quantity: int
    from_node: str
    to_node: str
    week_shipped: int
    week_to_arrive: int


class SupplyChainNode(ABC):
    """Abstract base class for all supply chain entities."""
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        node_type: NodeType,
        initial_inventory: int = 12,
        initial_backlog: int = 0,
        holding_cost_per_unit: float = 0.5,
        backlog_cost_per_unit: float = 1.0,
        lead_time: int = 2,
        order_delay: int = 2,
        shipment_delay: int = 2
    ):
        """
        Initialize a supply chain node.
        
        Args:
            env: SimPy environment
            name: Name of the node
            node_type: Type of the supply chain node
            initial_inventory: Starting inventory level
            initial_backlog: Starting backlog amount
            holding_cost_per_unit: Cost per unit of inventory held per week
            backlog_cost_per_unit: Cost per unit of backlog per week
            lead_time: Total lead time for orders (order + shipment delay)
            order_delay: Delay in weeks for order processing
            shipment_delay: Delay in weeks for shipment arrival
        """
        self.env = env
        self.name = name
        self.node_type = node_type
        
        # Inventory management
        self.inventory = initial_inventory
        self.backlog = initial_backlog
        self.holding_cost_per_unit = holding_cost_per_unit
        self.backlog_cost_per_unit = backlog_cost_per_unit
        
        # Lead times
        self.lead_time = lead_time
        self.order_delay = order_delay
        self.shipment_delay = shipment_delay
        
        # Orders and shipments tracking
        self.pending_orders: List[Order] = []
        self.incoming_shipments: List[Shipment] = []
        self.outgoing_shipments: List[Shipment] = []
        self.orders_placed: List[Order] = []
        self.orders_received: List[Order] = []
        
        # Connections to other nodes
        self.upstream_node: Optional['SupplyChainNode'] = None
        self.downstream_node: Optional['SupplyChainNode'] = None
        
        # Metrics tracking
        self.history: Dict[str, List[Any]] = {
            'week': [],
            'inventory': [],
            'backlog': [],
            'orders_placed': [],
            'orders_received': [],
            'shipments_sent': [],
            'shipments_received': [],
            'holding_cost': [],
            'backlog_cost': [],
            'total_cost': []
        }
        
        # Start the node's process
        self.process = env.process(self.run())
    
    def connect_upstream(self, node: 'SupplyChainNode'):
        """Connect to an upstream node (supplier)."""
        self.upstream_node = node
        node.downstream_node = self
    
    def connect_downstream(self, node: 'SupplyChainNode'):
        """Connect to a downstream node (customer)."""
        self.downstream_node = node
        node.upstream_node = self
    
    def place_order(self, quantity: int):
        """
        Place an order to the upstream node.
        
        Args:
            quantity: Number of units to order
        """
        order = Order(
            quantity=quantity,
            week_placed=int(self.env.now),
            from_node=self.name,
            to_node=self.upstream_node.name if self.upstream_node else "external_supplier"
        )
        
        self.orders_placed.append(order)
        
        if self.upstream_node:
            # Schedule order arrival at upstream node after order delay
            order.week_to_arrive = int(self.env.now) + self.order_delay
            self.upstream_node.pending_orders.append(order)
    
    def receive_order(self, order: Order):
        """
        Receive and process an order from downstream node.
        
        Args:
            order: The order to process
        """
        self.orders_received.append(order)
        
        # Try to fulfill the order
        quantity_to_ship = min(order.quantity + self.backlog, self.inventory)
        
        if quantity_to_ship > 0:
            # Create shipment
            shipment = Shipment(
                quantity=quantity_to_ship,
                from_node=self.name,
                to_node=order.from_node,
                week_shipped=int(self.env.now),
                week_to_arrive=int(self.env.now) + self.shipment_delay
            )
            
            self.outgoing_shipments.append(shipment)
            self.inventory -= quantity_to_ship
            
            # Schedule shipment arrival at downstream node
            if self.downstream_node:
                self.downstream_node.incoming_shipments.append(shipment)
        
        # Update backlog
        unfulfilled = order.quantity + self.backlog - quantity_to_ship
        self.backlog = max(0, unfulfilled)
    
    def receive_shipment(self, shipment: Shipment):
        """
        Receive a shipment from upstream node.
        
        Args:
            shipment: The shipment to receive
        """
        self.inventory += shipment.quantity
    
    def calculate_costs(self) -> Dict[str, float]:
        """
        Calculate costs for the current period.
        
        Returns:
            Dictionary with holding_cost, backlog_cost, and total_cost
        """
        holding_cost = self.inventory * self.holding_cost_per_unit
        backlog_cost = self.backlog * self.backlog_cost_per_unit
        total_cost = holding_cost + backlog_cost
        
        return {
            'holding_cost': holding_cost,
            'backlog_cost': backlog_cost,
            'total_cost': total_cost
        }
    
    def record_metrics(self):
        """Record current state metrics to history."""
        costs = self.calculate_costs()
        
        self.history['week'].append(int(self.env.now))
        self.history['inventory'].append(self.inventory)
        self.history['backlog'].append(self.backlog)
        self.history['orders_placed'].append(
            sum(o.quantity for o in self.orders_placed 
                if o.week_placed == int(self.env.now))
        )
        self.history['orders_received'].append(
            sum(o.quantity for o in self.orders_received 
                if o.week_placed == int(self.env.now))
        )
        self.history['shipments_sent'].append(
            sum(s.quantity for s in self.outgoing_shipments 
                if s.week_shipped == int(self.env.now))
        )
        self.history['shipments_received'].append(
            sum(s.quantity for s in self.incoming_shipments 
                if s.week_to_arrive == int(self.env.now))
        )
        self.history['holding_cost'].append(costs['holding_cost'])
        self.history['backlog_cost'].append(costs['backlog_cost'])
        self.history['total_cost'].append(costs['total_cost'])
    
    @abstractmethod
    def get_order_quantity(self, week: int) -> int:
        """
        Determine the order quantity for the current period.
        This method must be implemented by subclasses.
        
        Args:
            week: Current simulation week
            
        Returns:
            Quantity to order
        """
        pass
    
    def run(self):
        """Main process loop for the supply chain node."""
        while True:
            current_week = int(self.env.now)
            
            # Process incoming shipments that have arrived
            arrived_shipments = [
                s for s in self.incoming_shipments 
                if s.week_to_arrive == current_week
            ]
            for shipment in arrived_shipments:
                self.receive_shipment(shipment)
                self.incoming_shipments.remove(shipment)
            
            # Process pending orders that have arrived
            arrived_orders = [
                o for o in self.pending_orders 
                if o.week_to_arrive == current_week
            ]
            for order in arrived_orders:
                self.receive_order(order)
                self.pending_orders.remove(order)
            
            # Determine order quantity and place order
            order_quantity = self.get_order_quantity(current_week)
            if order_quantity > 0:
                self.place_order(order_quantity)
            
            # Record metrics for this period
            self.record_metrics()
            
            # Wait for next period
            yield self.env.timeout(1)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the node.
        
        Returns:
            Dictionary containing current node state
        """
        costs = self.calculate_costs()
        return {
            'name': self.name,
            'type': self.node_type.value,
            'inventory': self.inventory,
            'backlog': self.backlog,
            'pending_orders': len(self.pending_orders),
            'incoming_shipments': len(self.incoming_shipments),
            'last_order': self.orders_placed[-1].quantity if self.orders_placed else 0,
            'costs': costs,
            'week': int(self.env.now)
        }
