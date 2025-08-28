"""WebSocket handlers for real-time game updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Any, Optional
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        """Initialize connection manager."""
        # Active connections: game_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Player connections: player_id -> websocket
        self.player_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        game_id: str,
        player_id: Optional[str] = None
    ):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            game_id: Game ID
            player_id: Optional player ID
        """
        await websocket.accept()
        
        # Add to game connections
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)
        
        # Add to player connections if player_id provided
        if player_id:
            self.player_connections[player_id] = websocket
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "game_id": game_id,
            "player_id": player_id,
            "connected_at": datetime.now().isoformat()
        }
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "game_id": game_id,
                "player_id": player_id,
                "message": "Connected to game"
            },
            websocket
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        # Get connection info
        info = self.connection_info.get(websocket, {})
        game_id = info.get("game_id")
        player_id = info.get("player_id")
        
        # Remove from game connections
        if game_id and game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
        
        # Remove from player connections
        if player_id and player_id in self.player_connections:
            if self.player_connections[player_id] == websocket:
                del self.player_connections[player_id]
        
        # Remove connection info
        if websocket in self.connection_info:
            del self.connection_info[websocket]
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific connection.
        
        Args:
            message: Message to send
            websocket: Target WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_game(self, game_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all connections in a game.
        
        Args:
            game_id: Game ID
            message: Message to broadcast
        """
        if game_id in self.active_connections:
            # Add timestamp to message
            message["timestamp"] = datetime.now().isoformat()
            
            # Send to all connections in the game
            disconnected = []
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def send_to_player(self, player_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific player.
        
        Args:
            player_id: Player ID
            message: Message to send
        """
        if player_id in self.player_connections:
            websocket = self.player_connections[player_id]
            await self.send_personal_message(message, websocket)
    
    async def broadcast_game_update(self, game_id: str, update_type: str, data: Dict[str, Any]):
        """
        Broadcast a game update event.
        
        Args:
            game_id: Game ID
            update_type: Type of update
            data: Update data
        """
        message = {
            "type": "game_update",
            "update_type": update_type,
            "data": data
        }
        await self.broadcast_to_game(game_id, message)
    
    async def broadcast_week_complete(
        self,
        game_id: str,
        week: int,
        metrics: Dict[str, Any],
        node_states: Dict[str, Any]
    ):
        """
        Broadcast week completion event.
        
        Args:
            game_id: Game ID
            week: Current week
            metrics: Game metrics
            node_states: State of all nodes
        """
        message = {
            "type": "week_complete",
            "week": week,
            "metrics": metrics,
            "node_states": node_states
        }
        await self.broadcast_to_game(game_id, message)
    
    async def request_player_decision(
        self,
        player_id: str,
        week: int,
        node_state: Dict[str, Any]
    ):
        """
        Request a decision from a player.
        
        Args:
            player_id: Player ID
            week: Current week
            node_state: Current state of player's node
        """
        message = {
            "type": "decision_request",
            "week": week,
            "node_state": node_state,
            "message": f"Please submit your order for week {week}"
        }
        await self.send_to_player(player_id, message)
    
    async def send_decision_confirmation(
        self,
        player_id: str,
        week: int,
        order_quantity: int
    ):
        """
        Confirm a player's decision.
        
        Args:
            player_id: Player ID
            week: Current week
            order_quantity: Order quantity submitted
        """
        message = {
            "type": "decision_confirmation",
            "week": week,
            "order_quantity": order_quantity,
            "message": f"Order of {order_quantity} units confirmed for week {week}"
        }
        await self.send_to_player(player_id, message)
    
    async def broadcast_game_ended(
        self,
        game_id: str,
        reason: str,
        results: Dict[str, Any]
    ):
        """
        Broadcast game end event.
        
        Args:
            game_id: Game ID
            reason: Reason for game end
            results: Final game results
        """
        message = {
            "type": "game_ended",
            "reason": reason,
            "results": results
        }
        await self.broadcast_to_game(game_id, message)
    
    def get_connection_count(self, game_id: str) -> int:
        """
        Get number of active connections for a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Number of active connections
        """
        if game_id in self.active_connections:
            return len(self.active_connections[game_id])
        return 0


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    player_id: Optional[str] = None
):
    """
    WebSocket endpoint for real-time game updates.
    
    Args:
        websocket: WebSocket connection
        game_id: Game ID
        player_id: Optional player ID
    """
    # Connect
    await manager.connect(websocket, game_id, player_id)
    
    try:
        # Notify others of new connection
        await manager.broadcast_game_update(
            game_id,
            "player_connected",
            {"player_id": player_id, "count": manager.get_connection_count(game_id)}
        )
        
        # Keep connection alive and handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
            
            elif message_type == "decision":
                # Handle player decision
                await handle_player_decision(game_id, player_id, data)
            
            elif message_type == "chat":
                # Broadcast chat message
                await handle_chat_message(game_id, player_id, data)
            
            elif message_type == "request_state":
                # Send current game state
                await send_game_state(websocket, game_id)
            
            else:
                # Echo unknown messages
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        # Disconnect
        manager.disconnect(websocket)
        
        # Notify others
        await manager.broadcast_game_update(
            game_id,
            "player_disconnected",
            {"player_id": player_id, "count": manager.get_connection_count(game_id)}
        )


async def handle_player_decision(
    game_id: str,
    player_id: str,
    data: Dict[str, Any]
):
    """
    Handle player decision submitted via WebSocket.
    
    Args:
        game_id: Game ID
        player_id: Player ID
        data: Decision data
    """
    from .endpoints import games
    
    if game_id in games:
        game = games[game_id]
        
        # Submit decision
        order_quantity = data.get("order_quantity", 0)
        success = game.submit_player_decision(
            player_id,
            {"order_quantity": order_quantity}
        )
        
        if success:
            # Confirm to player
            await manager.send_decision_confirmation(
                player_id,
                game.state.current_week,
                order_quantity
            )
            
            # Broadcast update
            await manager.broadcast_game_update(
                game_id,
                "decision_submitted",
                {
                    "player_id": player_id,
                    "week": game.state.current_week
                }
            )


async def handle_chat_message(
    game_id: str,
    player_id: str,
    data: Dict[str, Any]
):
    """
    Handle chat message.
    
    Args:
        game_id: Game ID
        player_id: Player ID
        data: Chat message data
    """
    message = {
        "type": "chat",
        "player_id": player_id,
        "message": data.get("message", ""),
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_game(game_id, message)


async def send_game_state(websocket: WebSocket, game_id: str):
    """
    Send current game state to a connection.
    
    Args:
        websocket: WebSocket connection
        game_id: Game ID
    """
    from .endpoints import games
    
    if game_id in games:
        game = games[game_id]
        state = game.get_current_state()
        
        await websocket.send_json({
            "type": "game_state",
            "state": state
        })


class EventBus:
    """Event bus for game events."""
    
    def __init__(self):
        """Initialize event bus."""
        self.listeners: Dict[str, List[callable]] = {}
    
    def on(self, event_type: str, callback: callable):
        """
        Register an event listener.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    async def emit(self, event_type: str, data: Any):
        """
        Emit an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)


# Global event bus
event_bus = EventBus()


# Register event handlers
def setup_event_handlers():
    """Set up event handlers for game events."""
    
    async def on_week_complete(data):
        """Handle week complete event."""
        game_id = data.get("game_id")
        week = data.get("week")
        metrics = data.get("metrics")
        node_states = data.get("node_states")
        
        await manager.broadcast_week_complete(game_id, week, metrics, node_states)
    
    async def on_game_ended(data):
        """Handle game ended event."""
        game_id = data.get("game_id")
        reason = data.get("reason")
        results = data.get("results")
        
        await manager.broadcast_game_ended(game_id, reason, results)
    
    # Register handlers
    event_bus.on("week_complete", on_week_complete)
    event_bus.on("game_ended", on_game_ended)
