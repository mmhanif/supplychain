# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python project called "simulation" - a minimal Python application currently in early development stage. The project uses modern Python tooling with uv as the package manager and requires Python 3.10+.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (using uv)
uv venv
source .venv/bin/activate  # On macOS/Linux
# or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -e .
```

### Running the Application
```bash
# Run the main application
python main.py

# Or run as module
python -m simulation
```

### Development Tools
```bash
# Install development dependencies (when added to pyproject.toml)
uv pip install -e ".[dev]"

# Run tests (when test framework is added)
python -m pytest

# Run a single test file
python -m pytest test_filename.py

# Format code (if black/ruff is added)
ruff format .

# Lint code (if ruff is added)
ruff check .

# Type checking (if mypy is added)
mypy .
```

### Package Management
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv lock --upgrade
```

## Project Structure

Currently minimal structure:
- `main.py` - Entry point with main() function
- `pyproject.toml` - Project configuration and dependencies
- `README.md` - Project documentation (currently empty)
- `.python-version` - Python version specification (3.10)
- `.gitignore` - Git ignore patterns for Python projects

## Architecture Notes

This is a new project with a simple entry point architecture. As the project grows, consider organizing code into:
- A proper package structure under `src/simulation/` or `simulation/`
- Separate modules for different functionality
- Test directory with corresponding test files
- Configuration and data directories as needed

The project is configured for Python 3.10+ and uses modern Python packaging standards via pyproject.toml.
