"""Web interface for Beer Distribution Game."""

from .app import create_app
from .api import router as api_router

__all__ = ["create_app", "api_router"]
