"""Metrics collection and analysis for the simulation."""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SimulationMetrics:
    """Container for simulation-wide metrics."""
    
    simulation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_weeks: int = 0
    
    # Aggregate metrics
    total_cost: float = 0.0
    total_holding_cost: float = 0.0
    total_backlog_cost: float = 0.0
    
    # Service level metrics
    fill_rate: float = 0.0
    stockout_weeks: int = 0
    
    # Bullwhip effect
    bullwhip_ratio: float = 0.0
    
    # Node-specific histories
    node_histories: Dict[str, Dict[str, List[Any]]] = field(default_factory=dict)


class MetricsCollector:
    """Collects and analyzes metrics from the simulation."""
    
    def __init__(self, simulation_id: str):
        """
        Initialize the metrics collector.
        
        Args:
            simulation_id: Unique identifier for the simulation
        """
        self.simulation_id = simulation_id
        self.metrics = SimulationMetrics(
            simulation_id=simulation_id,
            start_time=datetime.now()
        )
        self.nodes = []
    
    def register_node(self, node):
        """
        Register a supply chain node for metrics collection.
        
        Args:
            node: SupplyChainNode to monitor
        """
        self.nodes.append(node)
        self.metrics.node_histories[node.name] = {
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
    
    def collect_current_metrics(self, week: int):
        """
        Collect metrics for the current simulation week.
        
        Args:
            week: Current simulation week
        """
        self.metrics.total_weeks = week
        
        for node in self.nodes:
            # Copy node's history to our metrics
            for key in node.history:
                if node.history[key]:  # Only if there's data
                    self.metrics.node_histories[node.name][key] = node.history[key].copy()
            
            # Calculate cumulative costs
            if node.history['total_cost']:
                node_total_cost = sum(node.history['total_cost'])
                node_holding_cost = sum(node.history['holding_cost'])
                node_backlog_cost = sum(node.history['backlog_cost'])
                
                self.metrics.total_cost += node_total_cost
                self.metrics.total_holding_cost += node_holding_cost
                self.metrics.total_backlog_cost += node_backlog_cost
    
    def calculate_bullwhip_effect(self) -> float:
        """
        Calculate the bullwhip effect ratio.
        
        Returns:
            Ratio of order variance amplification through the supply chain
        """
        if not self.nodes or self.metrics.total_weeks < 10:
            return 0.0
        
        # Get retailer (downstream) and factory (upstream) order variances
        retailer_orders = []
        factory_orders = []
        
        for node in self.nodes:
            if node.node_type.value == "retailer":
                retailer_orders = self.metrics.node_histories[node.name]['orders_placed']
            elif node.node_type.value == "factory":
                factory_orders = self.metrics.node_histories[node.name]['orders_placed']
        
        if len(retailer_orders) > 1 and len(factory_orders) > 1:
            retailer_var = np.var(retailer_orders)
            factory_var = np.var(factory_orders)
            
            if retailer_var > 0:
                self.metrics.bullwhip_ratio = factory_var / retailer_var
            else:
                self.metrics.bullwhip_ratio = 0.0
        
        return self.metrics.bullwhip_ratio
    
    def calculate_service_levels(self) -> Dict[str, float]:
        """
        Calculate service level metrics for each node.
        
        Returns:
            Dictionary of service levels by node
        """
        service_levels = {}
        
        for node in self.nodes:
            history = self.metrics.node_histories[node.name]
            
            if history['orders_received'] and history['backlog']:
                total_demand = sum(history['orders_received'])
                total_backlog = sum(history['backlog'])
                stockout_weeks = sum(1 for b in history['backlog'] if b > 0)
                
                if total_demand > 0:
                    fill_rate = 1 - (total_backlog / total_demand)
                else:
                    fill_rate = 1.0
                
                service_levels[node.name] = {
                    'fill_rate': fill_rate,
                    'stockout_weeks': stockout_weeks,
                    'stockout_percentage': stockout_weeks / max(1, len(history['backlog']))
                }
        
        # Calculate overall fill rate
        if service_levels:
            avg_fill_rate = np.mean([sl['fill_rate'] for sl in service_levels.values()])
            self.metrics.fill_rate = avg_fill_rate
            
            total_stockout_weeks = sum(sl['stockout_weeks'] for sl in service_levels.values())
            self.metrics.stockout_weeks = total_stockout_weeks
        
        return service_levels
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for the simulation.
        
        Returns:
            Dictionary of summary statistics
        """
        self.calculate_bullwhip_effect()
        service_levels = self.calculate_service_levels()
        
        return {
            'simulation_id': self.simulation_id,
            'total_weeks': self.metrics.total_weeks,
            'total_cost': self.metrics.total_cost,
            'total_holding_cost': self.metrics.total_holding_cost,
            'total_backlog_cost': self.metrics.total_backlog_cost,
            'average_cost_per_week': self.metrics.total_cost / max(1, self.metrics.total_weeks),
            'fill_rate': self.metrics.fill_rate,
            'stockout_weeks': self.metrics.stockout_weeks,
            'bullwhip_ratio': self.metrics.bullwhip_ratio,
            'service_levels': service_levels
        }
    
    def get_time_series_data(self) -> pd.DataFrame:
        """
        Get time series data for all nodes as a pandas DataFrame.
        
        Returns:
            DataFrame with time series data
        """
        data_frames = []
        
        for node_name, history in self.metrics.node_histories.items():
            if history['week']:  # Only if there's data
                df = pd.DataFrame(history)
                df['node'] = node_name
                data_frames.append(df)
        
        if data_frames:
            return pd.concat(data_frames, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def get_node_summary(self, node_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a specific node.
        
        Args:
            node_name: Name of the node
            
        Returns:
            Dictionary of node-specific statistics
        """
        if node_name not in self.metrics.node_histories:
            return {}
        
        history = self.metrics.node_histories[node_name]
        
        if not history['week']:
            return {}
        
        return {
            'node': node_name,
            'average_inventory': np.mean(history['inventory']),
            'max_inventory': max(history['inventory']),
            'min_inventory': min(history['inventory']),
            'average_backlog': np.mean(history['backlog']),
            'max_backlog': max(history['backlog']),
            'total_orders_placed': sum(history['orders_placed']),
            'total_orders_received': sum(history['orders_received']),
            'total_cost': sum(history['total_cost']),
            'average_cost_per_week': np.mean(history['total_cost'])
        }
    
    def export_to_json(self) -> Dict[str, Any]:
        """
        Export all metrics to a JSON-serializable dictionary.
        
        Returns:
            Dictionary containing all metrics data
        """
        return {
            'summary': self.get_summary_statistics(),
            'node_summaries': {
                node.name: self.get_node_summary(node.name) 
                for node in self.nodes
            },
            'time_series': self.metrics.node_histories
        }
    
    def finalize(self):
        """Finalize metrics collection."""
        self.metrics.end_time = datetime.now()
        self.calculate_bullwhip_effect()
        self.calculate_service_levels()
