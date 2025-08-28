#!/usr/bin/env python
"""Run the Beer Distribution Game web server."""

import uvicorn
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.web.app import app


def main():
    """Run the web server."""
    print("=" * 60)
    print("  Beer Distribution Game - Web Interface")
    print("=" * 60)
    print()
    print("Starting server...")
    print("Once started, open http://localhost:8000 in your browser")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
