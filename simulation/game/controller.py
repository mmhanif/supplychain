"""Game Controller for managing game rules and state."""

import uuid
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import json

from ..engine import SimulationEnvironment
from ..engine.core import SimulationConfig, SimulationStatus


class GameStatus(Enum):
    """Game status enumeration."""
    SETUP = "setup"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PlayerRole(Enum):
    """Player roles in the supply chain."""
    RETAILER = "retailer"
    WHOLESALER = "wholesaler"
    DISTRIBUTOR = "distributor"
    FACTORY = "factory"
    ALL = "all"  # For single player controlling all nodes
    OBSERVER = "observer"  # For viewing only


@dataclass
class Player:
    """Represents a player in the game."""
    id: str
    name: str
    role: PlayerRole
    is_human: bool = True
    is_active: bool = True
    score: float = 0.0
    decisions_made: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameRules:
    """Game rules and win conditions."""
    max_weeks: int = 52
    target_service_level: float = 0.95
    max_total_cost: Optional[float] = None
    allow_negative_inventory: bool = False
    enable_information_sharing: bool = False
    enable_forecasting: bool = False
    cost_penalty_multiplier: float = 1.0
    
    # Win conditions
    minimize_cost: bool = True
    maximize_service_level: bool = True
    minimize_bullwhip: bool = False
    
    # Game modes
    competitive_mode: bool = False  # Players compete against each other
    collaborative_mode: bool = True  # Players work together
    tutorial_mode: bool = False
    
    # Time limits
    decision_time_limit: Optional[int] = None  # Seconds per decision
    game_time_limit: Optional[int] = None  # Total game time in minutes


@dataclass
class GameState:
    """Current state of the game."""
    game_id: str
    status: GameStatus
    current_week: int
    total_weeks: int
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Players
    players: Dict[str, Player] = field(default_factory=dict)
    
    # Scores and metrics
    total_cost: float = 0.0
    total_holding_cost: float = 0.0
    total_backlog_cost: float = 0.0
    service_level: float = 1.0
    bullwhip_ratio: float = 0.0
    
    # Node states
    node_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # History
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    event_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class GameController:
    """Controls game logic, rules, and win conditions."""
    
    def __init__(
        self,
        game_rules: Optional[GameRules] = None,
        simulation_config: Optional[SimulationConfig] = None
    ):
        """
        Initialize the game controller.
        
        Args:
            game_rules: Rules and win conditions for the game
            simulation_config: Configuration for the simulation
        """
        self.game_id = str(uuid.uuid4())
        self.rules = game_rules or GameRules()
        self.simulation_config = simulation_config or SimulationConfig(weeks=self.rules.max_weeks)
        
        # Game state
        self.state = GameState(
            game_id=self.game_id,
            status=GameStatus.SETUP,
            current_week=0,
            total_weeks=self.rules.max_weeks,
            start_time=datetime.now()
        )
        
        # Simulation environment
        self.simulation: Optional[SimulationEnvironment] = None
        
        # Callbacks
        self.on_week_complete: Optional[Callable] = None
        self.on_game_complete: Optional[Callable] = None
        self.on_player_decision: Optional[Callable] = None
        
        # Decision queue for human players
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}
        self.decision_callbacks: Dict[str, Callable] = {}
    
    def add_player(
        self,
        name: str,
        role: PlayerRole,
        is_human: bool = True
    ) -> Player:
        """
        Add a player to the game.
        
        Args:
            name: Player name
            role: Player's role in the supply chain
            is_human: Whether the player is human or AI
            
        Returns:
            The created Player object
        """
        player_id = str(uuid.uuid4())
        player = Player(
            id=player_id,
            name=name,
            role=role,
            is_human=is_human
        )
        
        self.state.players[player_id] = player
        
        self._log_event({
            "type": "player_added",
            "player_id": player_id,
            "name": name,
            "role": role.value,
            "is_human": is_human
        })
        
        return player
    
    def remove_player(self, player_id: str):
        """Remove a player from the game."""
        if player_id in self.state.players:
            player = self.state.players[player_id]
            player.is_active = False
            
            self._log_event({
                "type": "player_removed",
                "player_id": player_id,
                "name": player.name
            })
    
    def initialize_game(self):
        """Initialize the game and prepare for start."""
        if self.state.status != GameStatus.SETUP:
            raise RuntimeError(f"Cannot initialize game in status {self.state.status}")
        
        # Create simulation environment
        self.simulation = SimulationEnvironment(self.simulation_config)
        
        # Set up callbacks
        self.simulation.on_week_complete = self._on_simulation_week_complete
        self.simulation.on_simulation_complete = self._on_simulation_complete
        
        # Configure policies based on players
        self._configure_node_policies()
        
        self.state.status = GameStatus.READY
        
        self._log_event({
            "type": "game_initialized",
            "game_id": self.game_id,
            "rules": self._rules_to_dict()
        })
    
    def start_game(self):
        """Start the game."""
        if self.state.status != GameStatus.READY:
            raise RuntimeError(f"Cannot start game in status {self.state.status}")
        
        self.state.status = GameStatus.IN_PROGRESS
        self.state.start_time = datetime.now()
        
        self._log_event({
            "type": "game_started",
            "game_id": self.game_id,
            "players": len(self.state.players)
        })
        
        # Start simulation
        if self.simulation:
            # Run simulation step by step for human interaction
            if self._has_human_players():
                self._run_interactive_simulation()
            else:
                # Run full simulation for AI-only games
                results = self.simulation.run()
                self._process_simulation_results(results)
    
    def pause_game(self):
        """Pause the game."""
        if self.state.status == GameStatus.IN_PROGRESS:
            self.state.status = GameStatus.PAUSED
            
            if self.simulation:
                self.simulation.pause()
            
            self._log_event({
                "type": "game_paused",
                "week": self.state.current_week
            })
    
    def resume_game(self):
        """Resume a paused game."""
        if self.state.status == GameStatus.PAUSED:
            self.state.status = GameStatus.IN_PROGRESS
            
            if self.simulation:
                self.simulation.resume()
            
            self._log_event({
                "type": "game_resumed",
                "week": self.state.current_week
            })
    
    def end_game(self, reason: str = "completed"):
        """
        End the game.
        
        Args:
            reason: Reason for ending (completed, abandoned, etc.)
        """
        if self.state.status in [GameStatus.IN_PROGRESS, GameStatus.PAUSED]:
            self.state.status = GameStatus.COMPLETED if reason == "completed" else GameStatus.ABANDONED
            self.state.end_time = datetime.now()
            
            # Calculate final scores
            self._calculate_final_scores()
            
            self._log_event({
                "type": "game_ended",
                "reason": reason,
                "final_week": self.state.current_week,
                "total_cost": self.state.total_cost
            })
            
            if self.on_game_complete:
                self.on_game_complete(self.state)
    
    def submit_player_decision(
        self,
        player_id: str,
        decision: Dict[str, Any]
    ) -> bool:
        """
        Submit a player's decision for the current week.
        
        Args:
            player_id: ID of the player
            decision: Decision data (e.g., order quantity)
            
        Returns:
            True if decision was accepted
        """
        if player_id not in self.state.players:
            return False
        
        player = self.state.players[player_id]
        
        # Record decision
        self.state.decision_history.append({
            "week": self.state.current_week,
            "player_id": player_id,
            "role": player.role.value,
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        })
        
        player.decisions_made += 1
        
        # Apply decision to simulation
        self._apply_player_decision(player, decision)
        
        self._log_event({
            "type": "decision_submitted",
            "player_id": player_id,
            "week": self.state.current_week,
            "decision": decision
        })
        
        if self.on_player_decision:
            self.on_player_decision(player_id, decision)
        
        # Check if all decisions are in
        if self._all_decisions_received():
            self._advance_simulation()
        
        return True
    
    def get_player_view(self, player_id: str) -> Dict[str, Any]:
        """
        Get the game state from a player's perspective.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Game state visible to the player
        """
        if player_id not in self.state.players:
            return {}
        
        player = self.state.players[player_id]
        
        # Basic game info
        view = {
            "game_id": self.game_id,
            "status": self.state.status.value,
            "current_week": self.state.current_week,
            "total_weeks": self.state.total_weeks,
            "player": {
                "id": player.id,
                "name": player.name,
                "role": player.role.value,
                "score": player.score
            }
        }
        
        # Node state based on role
        if player.role != PlayerRole.OBSERVER:
            if player.role == PlayerRole.ALL:
                view["nodes"] = self.state.node_states
            else:
                node_name = player.role.value.capitalize()
                if node_name in self.state.node_states:
                    view["node_state"] = self.state.node_states[node_name]
            
            # Limited visibility based on information sharing
            if self.rules.enable_information_sharing:
                view["supply_chain_state"] = self.state.node_states
            else:
                # Only see immediate upstream/downstream
                view["upstream_backlog"] = self._get_upstream_backlog(player.role)
                view["downstream_demand"] = self._get_downstream_demand(player.role)
        
        # Costs and metrics
        view["metrics"] = {
            "total_cost": self.state.total_cost,
            "service_level": self.state.service_level,
            "bullwhip_ratio": self.state.bullwhip_ratio
        }
        
        return view
    
    def calculate_costs(self) -> Dict[str, float]:
        """
        Calculate current costs.
        
        Returns:
            Dictionary of cost components
        """
        if not self.simulation:
            return {}
        
        total_holding = 0.0
        total_backlog = 0.0
        
        for node in self.simulation.nodes:
            costs = node.calculate_costs()
            total_holding += costs["holding_cost"]
            total_backlog += costs["backlog_cost"]
        
        # Apply penalty multiplier
        total_backlog *= self.rules.cost_penalty_multiplier
        
        total = total_holding + total_backlog
        
        return {
            "holding_cost": total_holding,
            "backlog_cost": total_backlog,
            "total_cost": total,
            "average_cost_per_week": total / max(1, self.state.current_week)
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the game.
        
        Returns:
            Dictionary containing current game state
        """
        # Get node states from simulation if available
        node_states = {}
        if self.simulation:
            for node in self.simulation.nodes:
                node_states[node.name] = {
                    "inventory": node.inventory,
                    "backlog": node.backlog,
                    "last_order": node.orders_placed[-1].quantity if node.orders_placed else 0,
                    "pending_orders": len(node.pending_orders),
                    "incoming_shipments": len(node.incoming_shipments)
                }
        
        return {
            "game_id": self.game_id,
            "current_week": self.state.current_week,
            "total_weeks": self.state.total_weeks,
            "status": self.state.status.value,
            "nodes": node_states or self.state.node_states,
            "metrics": {
                "total_cost": self.state.total_cost,
                "service_level": self.state.service_level,
                "bullwhip_ratio": self.state.bullwhip_ratio
            },
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "role": p.role.value,
                    "score": p.score
                }
                for p in self.state.players.values()
            ]
        }
    
    def check_win_conditions(self) -> Dict[str, Any]:
        """
        Check if win conditions are met.
        
        Returns:
            Dictionary with win condition status
        """
        conditions_met = {}
        
        if self.rules.minimize_cost and self.rules.max_total_cost:
            conditions_met["cost_target"] = self.state.total_cost <= self.rules.max_total_cost
        
        if self.rules.maximize_service_level:
            conditions_met["service_target"] = self.state.service_level >= self.rules.target_service_level
        
        if self.rules.minimize_bullwhip:
            conditions_met["bullwhip_target"] = self.state.bullwhip_ratio <= 2.0
        
        all_met = all(conditions_met.values()) if conditions_met else False
        
        return {
            "all_conditions_met": all_met,
            "conditions": conditions_met,
            "game_complete": self.state.current_week >= self.state.total_weeks
        }
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Get player leaderboard.
        
        Returns:
            List of players sorted by score
        """
        leaderboard = []
        
        for player in self.state.players.values():
            leaderboard.append({
                "rank": 0,  # Will be set after sorting
                "player_id": player.id,
                "name": player.name,
                "role": player.role.value,
                "score": player.score,
                "decisions_made": player.decisions_made
            })
        
        # Sort by score (higher is better)
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Set ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard
    
    def export_game_data(self) -> Dict[str, Any]:
        """
        Export complete game data.
        
        Returns:
            Complete game data as dictionary
        """
        return {
            "game_id": self.game_id,
            "status": self.state.status.value,
            "rules": self._rules_to_dict(),
            "players": [self._player_to_dict(p) for p in self.state.players.values()],
            "state": {
                "current_week": self.state.current_week,
                "total_weeks": self.state.total_weeks,
                "total_cost": self.state.total_cost,
                "service_level": self.state.service_level,
                "bullwhip_ratio": self.state.bullwhip_ratio
            },
            "history": {
                "decisions": self.state.decision_history,
                "events": self.state.event_log
            },
            "results": self.simulation.get_results() if self.simulation else None
        }
    
    def save_game(self, filepath: str):
        """Save game state to file."""
        game_data = self.export_game_data()
        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2, default=str)
    
    def _configure_node_policies(self):
        """Configure node policies based on players."""
        if not self.simulation:
            return
        
        # Map players to nodes and set appropriate policies
        for player in self.state.players.values():
            if player.role == PlayerRole.RETAILER:
                if player.is_human:
                    self.simulation.retailer.order_policy = lambda week: self._request_human_decision(player.id, week)
            elif player.role == PlayerRole.WHOLESALER:
                if player.is_human:
                    self.simulation.wholesaler.order_policy = lambda week: self._request_human_decision(player.id, week)
            # Continue for other roles...
    
    def _has_human_players(self) -> bool:
        """Check if there are human players."""
        return any(p.is_human for p in self.state.players.values())
    
    def _run_interactive_simulation(self):
        """Run simulation with human interaction."""
        # This would implement step-by-step simulation
        # For now, we'll use the regular simulation
        if self.simulation:
            results = self.simulation.run()
            self._process_simulation_results(results)
    
    def _request_human_decision(self, player_id: str, week: int) -> int:
        """Request decision from human player."""
        # In a real implementation, this would pause and wait for input
        # For now, return a default value
        return 4
    
    def _all_decisions_received(self) -> bool:
        """Check if all human players have submitted decisions."""
        for player in self.state.players.values():
            if player.is_human and player.is_active:
                # Check if decision received for current week
                # Implementation depends on decision tracking
                pass
        return True
    
    def _advance_simulation(self):
        """Advance simulation by one week."""
        if self.simulation and self.simulation.env:
            # Get current simulation time
            current_time = self.simulation.env.now
            next_time = current_time + 1
            
            # Check if we're within the game limits
            if next_time <= self.state.total_weeks:
                # Run simulation until next week
                self.simulation.env.run(until=next_time)
                self.state.current_week = int(self.simulation.env.now)
                
                # Update game state from simulation
                sim_state = self.simulation.get_current_state()
                self._on_simulation_week_complete(sim_state)
            else:
                # Game has reached the end
                self.end_game("completed")
    
    def _apply_player_decision(self, player: Player, decision: Dict[str, Any]):
        """Apply player decision to simulation."""
        # Implementation depends on decision structure
        pass
    
    def _get_upstream_backlog(self, role: PlayerRole) -> float:
        """Get upstream node's backlog."""
        if not self.simulation:
            return 0.0
        
        # Map role to upstream node
        upstream_map = {
            PlayerRole.RETAILER: self.simulation.wholesaler,
            PlayerRole.WHOLESALER: self.simulation.distributor,
            PlayerRole.DISTRIBUTOR: self.simulation.factory
        }
        
        upstream = upstream_map.get(role)
        return upstream.backlog if upstream else 0.0
    
    def _get_downstream_demand(self, role: PlayerRole) -> float:
        """Get downstream node's demand."""
        # Implementation depends on demand visibility rules
        return 4.0  # Default
    
    def _calculate_final_scores(self):
        """Calculate final scores for all players."""
        if not self.simulation:
            return
        
        # Base score calculation
        max_possible_score = 10000.0
        cost_penalty = min(self.state.total_cost, max_possible_score)
        
        for player in self.state.players.values():
            # Score based on performance
            base_score = max_possible_score - cost_penalty
            
            # Bonus for service level
            service_bonus = self.state.service_level * 1000
            
            # Penalty for bullwhip effect
            bullwhip_penalty = min(self.state.bullwhip_ratio * 100, 1000)
            
            player.score = max(0, base_score + service_bonus - bullwhip_penalty)
    
    def _on_simulation_week_complete(self, sim_state: Dict[str, Any]):
        """Handle simulation week completion."""
        self.state.current_week = sim_state["current_week"]
        
        # Update costs
        costs = self.calculate_costs()
        self.state.total_cost = costs["total_cost"]
        self.state.total_holding_cost = costs["holding_cost"]
        self.state.total_backlog_cost = costs["backlog_cost"]
        
        # Update metrics
        if "metrics" in sim_state:
            metrics = sim_state["metrics"]
            self.state.service_level = metrics.get("fill_rate", 1.0)
            self.state.bullwhip_ratio = metrics.get("bullwhip_ratio", 0.0)
        
        # Update node states
        if "nodes" in sim_state:
            self.state.node_states = sim_state["nodes"]
        
        # Check win conditions
        win_status = self.check_win_conditions()
        if win_status["game_complete"]:
            self.end_game("completed")
        
        # Trigger callback
        if self.on_week_complete:
            self.on_week_complete(self.state)
    
    def _on_simulation_complete(self, results: Dict[str, Any]):
        """Handle simulation completion."""
        self._process_simulation_results(results)
        self.end_game("completed")
    
    def _process_simulation_results(self, results: Dict[str, Any]):
        """Process final simulation results."""
        if "summary" in results:
            summary = results["summary"]
            self.state.total_cost = summary.get("total_cost", 0)
            self.state.service_level = summary.get("fill_rate", 1.0)
            self.state.bullwhip_ratio = summary.get("bullwhip_ratio", 0.0)
    
    def _log_event(self, event: Dict[str, Any]):
        """Log a game event."""
        event["timestamp"] = datetime.now().isoformat()
        event["week"] = self.state.current_week
        self.state.event_log.append(event)
    
    def _rules_to_dict(self) -> Dict[str, Any]:
        """Convert game rules to dictionary."""
        return {
            "max_weeks": self.rules.max_weeks,
            "target_service_level": self.rules.target_service_level,
            "max_total_cost": self.rules.max_total_cost,
            "competitive_mode": self.rules.competitive_mode,
            "collaborative_mode": self.rules.collaborative_mode,
            "tutorial_mode": self.rules.tutorial_mode
        }
    
    def _player_to_dict(self, player: Player) -> Dict[str, Any]:
        """Convert player to dictionary."""
        return {
            "id": player.id,
            "name": player.name,
            "role": player.role.value,
            "is_human": player.is_human,
            "is_active": player.is_active,
            "score": player.score,
            "decisions_made": player.decisions_made
        }
