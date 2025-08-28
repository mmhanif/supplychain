"""REST API endpoints for Beer Distribution Game."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from ...game import (
    GameController, GameRules, PlayerRole, GameStatus,
    PolicyManager, PolicyType,
    ScenarioManager, DifficultyLevel
)
from ...engine.core import SimulationConfig


# Pydantic models for API requests/responses
class GameConfigRequest(BaseModel):
    """Request model for game configuration."""
    scenario_id: str = "classic"
    max_weeks: int = 52
    target_service_level: float = 0.95
    max_total_cost: Optional[float] = None
    enable_information_sharing: bool = False
    enable_forecasting: bool = False
    collaborative_mode: bool = True
    tutorial_mode: bool = False


class PlayerRequest(BaseModel):
    """Request model for adding a player."""
    name: str
    role: str = Field(..., description="Player role: retailer, wholesaler, distributor, factory")
    is_human: bool = True
    policy_type: Optional[str] = None


class DecisionRequest(BaseModel):
    """Request model for player decision."""
    player_id: str
    order_quantity: int = Field(..., ge=0, description="Order quantity must be non-negative")
    week: Optional[int] = None


class ScenarioCreateRequest(BaseModel):
    """Request model for creating custom scenario."""
    name: str
    description: str
    demand_type: str = "constant"
    demand_params: Dict[str, Any]
    duration: int = 52
    difficulty: str = "medium"
    initial_inventory: int = 12
    holding_cost: float = 0.5
    backlog_cost: float = 1.0


# Global game storage (in production, use a proper database)
games: Dict[str, GameController] = {}
scenario_manager = ScenarioManager()
policy_manager = PolicyManager()


# Create API router
router = APIRouter(prefix="/api", tags=["game"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Beer Distribution Game API",
        "version": "1.0.0",
        "status": "online"
    }


@router.get("/scenarios")
async def list_scenarios(
    difficulty: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """List available scenarios."""
    difficulty_filter = DifficultyLevel(difficulty) if difficulty else None
    scenarios = scenario_manager.list_scenarios(
        difficulty=difficulty_filter,
        tags=tags
    )
    return {"scenarios": scenarios, "count": len(scenarios)}


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario."""
    scenario = scenario_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return {
        "id": scenario_id,
        "name": scenario.name,
        "description": scenario.description,
        "type": scenario.type.value,
        "difficulty": scenario.difficulty.value,
        "duration": scenario.duration_weeks,
        "demand_type": scenario.demand_type,
        "tags": scenario.tags,
        "hints": scenario.hints
    }


@router.post("/scenarios")
async def create_scenario(request: ScenarioCreateRequest):
    """Create a custom scenario."""
    config = {
        "demand_type": request.demand_type,
        "demand_params": request.demand_params,
        "duration": request.duration,
        "difficulty": request.difficulty,
        "initial_inventory": request.initial_inventory,
        "holding_cost": request.holding_cost,
        "backlog_cost": request.backlog_cost
    }
    
    scenario_id = scenario_manager.create_custom_scenario(
        request.name,
        request.description,
        config
    )
    
    return {"scenario_id": scenario_id, "message": "Scenario created successfully"}


@router.post("/games")
async def create_game(request: GameConfigRequest):
    """Create a new game."""
    # Get scenario
    scenario = scenario_manager.get_scenario(request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="Invalid scenario ID")
    
    # Create simulation config
    sim_config = scenario_manager.create_simulation_config(request.scenario_id)
    
    # Create game rules
    rules = GameRules(
        max_weeks=request.max_weeks,
        target_service_level=request.target_service_level,
        max_total_cost=request.max_total_cost,
        enable_information_sharing=request.enable_information_sharing,
        enable_forecasting=request.enable_forecasting,
        collaborative_mode=request.collaborative_mode,
        tutorial_mode=request.tutorial_mode
    )
    
    # Create game controller
    game = GameController(game_rules=rules, simulation_config=sim_config)
    
    # Store game
    games[game.game_id] = game
    
    return {
        "game_id": game.game_id,
        "status": game.state.status.value,
        "scenario": scenario.name,
        "max_weeks": rules.max_weeks
    }


@router.get("/games")
async def list_games():
    """List all games."""
    game_list = []
    for game_id, game in games.items():
        game_list.append({
            "game_id": game_id,
            "status": game.state.status.value,
            "current_week": game.state.current_week,
            "players": len(game.state.players),
            "total_cost": game.state.total_cost
        })
    
    return {"games": game_list, "count": len(game_list)}


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get game details."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    return {
        "game_id": game_id,
        "status": game.state.status.value,
        "current_week": game.state.current_week,
        "total_weeks": game.state.total_weeks,
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role.value,
                "is_human": p.is_human,
                "score": p.score
            }
            for p in game.state.players.values()
        ],
        "metrics": {
            "total_cost": game.state.total_cost,
            "service_level": game.state.service_level,
            "bullwhip_ratio": game.state.bullwhip_ratio
        }
    }


@router.post("/games/{game_id}/players")
async def add_player(game_id: str, request: PlayerRequest):
    """Add a player to the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state.status != GameStatus.SETUP:
        raise HTTPException(status_code=400, detail="Can only add players during setup")
    
    # Parse role
    try:
        role = PlayerRole(request.role.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
    
    # Add player
    player = game.add_player(request.name, role, request.is_human)
    
    # If AI player with policy, configure it
    if not request.is_human and request.policy_type:
        # This would be configured when game starts
        pass
    
    return {
        "player_id": player.id,
        "name": player.name,
        "role": player.role.value
    }


@router.post("/games/{game_id}/start")
async def start_game(game_id: str, background_tasks: BackgroundTasks):
    """Start the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state.status != GameStatus.SETUP:
        if game.state.status == GameStatus.READY:
            # Initialize if needed
            game.initialize_game()
        else:
            raise HTTPException(status_code=400, detail=f"Cannot start game in status {game.state.status.value}")
    else:
        game.initialize_game()
    
    # Start game in background
    background_tasks.add_task(game.start_game)
    
    return {
        "game_id": game_id,
        "status": "starting",
        "message": "Game is starting"
    }


@router.post("/games/{game_id}/stop")
async def stop_game(game_id: str):
    """Stop the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    game.end_game("stopped")
    
    return {
        "game_id": game_id,
        "status": game.state.status.value,
        "message": "Game stopped"
    }


@router.post("/games/{game_id}/pause")
async def pause_game(game_id: str):
    """Pause the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    game.pause_game()
    
    return {
        "game_id": game_id,
        "status": game.state.status.value,
        "message": "Game paused"
    }


@router.post("/games/{game_id}/resume")
async def resume_game(game_id: str):
    """Resume the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    game.resume_game()
    
    return {
        "game_id": game_id,
        "status": game.state.status.value,
        "message": "Game resumed"
    }


@router.post("/games/{game_id}/decisions")
async def submit_decision(game_id: str, request: DecisionRequest):
    """Submit a player decision."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game is not in progress")
    
    # Submit decision
    success = game.submit_player_decision(
        request.player_id,
        {"order_quantity": request.order_quantity}
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to submit decision")
    
    return {
        "success": True,
        "message": "Decision submitted",
        "week": game.state.current_week
    }


@router.get("/games/{game_id}/state")
async def get_game_state(game_id: str):
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    state = game.get_current_state()
    
    return state


@router.get("/games/{game_id}/results")
async def get_results(game_id: str):
    """Get game results."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state.status not in [GameStatus.COMPLETED, GameStatus.ABANDONED]:
        return {
            "status": "in_progress",
            "message": "Game is still in progress"
        }
    
    return {
        "status": "complete",
        "results": game.export_game_data()
    }


@router.get("/games/{game_id}/leaderboard")
async def get_leaderboard(game_id: str):
    """Get game leaderboard."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    leaderboard = game.get_leaderboard()
    
    return {
        "game_id": game_id,
        "week": game.state.current_week,
        "leaderboard": leaderboard
    }


@router.get("/games/{game_id}/player/{player_id}")
async def get_player_view(game_id: str, player_id: str):
    """Get player-specific view of the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    view = game.get_player_view(player_id)
    
    if not view:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return view


@router.get("/policies")
async def list_policies():
    """List available ordering policies."""
    policies = []
    for policy_type in PolicyType:
        info = policy_manager.get_policy_info(policy_type)
        policies.append({
            "type": policy_type.value,
            "name": info["name"],
            "description": info["description"],
            "parameters": info["parameters"]
        })
    
    return {"policies": policies}


@router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    
    return {"message": "Game deleted successfully"}
