# Setup Instructions

This document explains how to use the automated setup script and poetry configuration.

## Quick Start

### Using the Setup Script

The `setup_and_run.py` script automates the entire setup process:

```bash
# Setup and run with default command (probe --help)
python setup_and_run.py

# Setup and run with custom command
python setup_and_run.py --command "probe --host localhost --port 3000"

# Clean install (removes existing venv)
python setup_and_run.py --clean

# Setup only (don't run any command)
python setup_and_run.py --no-run
```

### What the Script Does

1. **Creates a virtual environment** in `.venv/` (if it doesn't exist)
2. **Installs Poetry** in the virtual environment
3. **Installs all dependencies** using `poetry install`
4. **Runs the specified command** using `poetry run`

## Poetry Configuration

The `pyproject.toml` file has been updated with Poetry configuration:

### Available Poetry Scripts

```bash
# After setup, you can use the 'probe' script:
poetry run probe --help
poetry run probe --host localhost --port 3000 --api-key sk-...
```

### Manual Poetry Commands

If you prefer to use Poetry directly:

```bash
# Create/activate virtual environment
poetry env use python3.10

# Install dependencies
poetry install

# Run the probe tool
poetry run probe --help

# Run with custom arguments
poetry run probe --host localhost --port 3000

# Run Python module directly
poetry run python -m local_assistant_probe.probe --help

# Run development tools
poetry run mypy local_assistant_probe
poetry run ruff check local_assistant_probe
```

## Environment Variables

You can use environment variables or a `.env` file for configuration:

```bash
cp .env.example .env
# Edit .env with your settings
```

Supported variables:
- `PROBE_HOST` - API host (default: localhost)
- `PROBE_PORT` - API port (default: 3000)
- `PROBE_API_KEY` - API key (required)
- `PROBE_MODEL_HINT` - Model hint to search for (default: llama3)
- `PROBE_TITLE` - Configuration title (default: Local Assistant)
- `PROBE_MODEL_NAME` - Model name for output (default: LLama3)
- `PROBE_TIMEOUT` - Request timeout in seconds (default: 3.0)
- `PROBE_DEBUG` - Enable debug output (default: false)

## Project Structure

```
local-assistant-probe/
├── pyproject.toml           # Poetry configuration with scripts
├── setup_and_run.py         # Automated setup script
├── local_assistant_probe/   # Main package
│   ├── __init__.py
│   └── probe.py            # Main probe logic
├── .env.example            # Example environment variables
└── README.md               # Project README
```

## Troubleshooting

### Poetry not found after installation

If poetry is not found as an executable, the script will automatically use it as a module:
```bash
python -m poetry --version
```

### Virtual environment issues

Clean and rebuild the virtual environment:
```bash
python setup_and_run.py --clean
```

### Permission errors on Unix/Linux/macOS

Make the script executable:
```bash
chmod +x setup_and_run.py
./setup_and_run.py
```

## Examples

### Basic usage with environment file

```bash
# 1. Copy and edit environment file
cp .env.example .env
nano .env  # or vim, code, etc.

# 2. Run the setup and probe
python setup_and_run.py --command "probe"
```

### Direct command-line usage

```bash
python setup_and_run.py --command "probe --host localhost --port 3000 --api-key sk-test123 --model-hint llama3"
```

### Development workflow

```bash
# Setup environment
python setup_and_run.py --no-run

# Activate the virtual environment
source .venv/bin/activate  # On Unix/Linux/macOS
# or
.venv\Scripts\activate.bat  # On Windows

# Use poetry commands directly
poetry run probe --help
poetry run mypy local_assistant_probe
poetry run ruff check local_assistant_probe
```

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
