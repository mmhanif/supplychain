"""FastAPI application for Beer Distribution Game."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from .api.endpoints import router as api_router
from .api.websocket import websocket_endpoint, manager, setup_event_handlers


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Beer Distribution Game",
        description="Web interface for the Beer Distribution Game simulation",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Get base directory
    base_dir = Path(__file__).resolve().parent
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
    
    # Include API routes
    app.include_router(api_router)
    
    # Root endpoint - serve index.html
    @app.get("/")
    async def read_index():
        """Serve the main HTML page."""
        return FileResponse(str(base_dir / "templates" / "index.html"))
    
    # WebSocket endpoints
    @app.websocket("/ws/{game_id}/{player_id}")
    async def websocket_game_with_player(websocket: WebSocket, game_id: str, player_id: str):
        """WebSocket endpoint for real-time game updates with player ID."""
        await websocket_endpoint(websocket, game_id, player_id)
    
    @app.websocket("/ws/{game_id}")
    async def websocket_game(websocket: WebSocket, game_id: str):
        """WebSocket endpoint for real-time game updates without player ID."""
        await websocket_endpoint(websocket, game_id, None)
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup."""
        setup_event_handlers()
        print("Beer Distribution Game server started")
        print("Open http://localhost:8000 in your browser")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up on shutdown."""
        print("Beer Distribution Game server shutting down")
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "simulation.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
