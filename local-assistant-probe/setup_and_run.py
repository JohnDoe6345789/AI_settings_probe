#!/usr/bin/env python3
"""
Setup script for local-assistant-probe

This script will:
1. Create a virtual environment (if it doesn't exist)
2. Install poetry in the virtual environment
3. Install project dependencies using poetry
4. Execute poetry run commands

Usage:
    python setup_and_run.py [--command COMMAND] [--clean]

Options:
    --command COMMAND : Poetry command to run (default: probe --help)
    --clean          : Remove existing venv and start fresh
    --no-run         : Only setup, don't run any command

Examples:
    python setup_and_run.py
    python setup_and_run.py --command "probe --host localhost --port 3000"
    python setup_and_run.py --clean
    python setup_and_run.py --no-run
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence


def _info(msg: str) -> None:
    """Print info message to stderr."""
    print(f"[INFO] {msg}", file=sys.stderr)


def _error(msg: str) -> None:
    """Print error message to stderr."""
    print(f"[ERROR] {msg}", file=sys.stderr)


def _run_command(cmd: List[str], cwd: Path | None = None) -> int:
    """Run a command and return exit code."""
    _info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError as e:
        _error(f"Command not found: {e}")
        return 1


def _get_venv_path(project_root: Path) -> Path:
    """Get the virtual environment path."""
    return project_root / ".venv"


def _get_python_executable(venv_path: Path) -> Path:
    """Get the python executable path in the venv."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def _get_poetry_executable(venv_path: Path) -> Path:
    """Get the poetry executable path in the venv."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "poetry.exe"
    return venv_path / "bin" / "poetry"


def _venv_exists(venv_path: Path) -> bool:
    """Check if virtual environment exists."""
    python_path = _get_python_executable(venv_path)
    return venv_path.exists() and python_path.exists()


def _create_venv(project_root: Path, venv_path: Path) -> int:
    """Create a virtual environment."""
    _info(f"Creating virtual environment at {venv_path}")
    return _run_command([sys.executable, "-m", "venv", str(venv_path)], cwd=project_root)


def _install_poetry(venv_path: Path) -> int:
    """Install poetry in the virtual environment."""
    python_path = _get_python_executable(venv_path)
    _info("Installing poetry...")
    return _run_command([str(python_path), "-m", "pip", "install", "poetry"])


def _poetry_is_installed(venv_path: Path) -> bool:
    """Check if poetry is installed in the venv."""
    poetry_path = _get_poetry_executable(venv_path)
    if not poetry_path.exists():
        python_path = _get_python_executable(venv_path)
        # Try running poetry as a module
        result = subprocess.run(
            [str(python_path), "-m", "poetry", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    return True


def _install_dependencies(project_root: Path, venv_path: Path) -> int:
    """Install project dependencies using poetry."""
    poetry_path = _get_poetry_executable(venv_path)
    python_path = _get_python_executable(venv_path)
    
    _info("Installing project dependencies with poetry...")
    
    # Use poetry as a module if executable not found
    if not poetry_path.exists():
        cmd = [str(python_path), "-m", "poetry", "install"]
    else:
        cmd = [str(poetry_path), "install"]
    
    return _run_command(cmd, cwd=project_root)


def _run_poetry_command(project_root: Path, venv_path: Path, command: str) -> int:
    """Run a poetry run command."""
    poetry_path = _get_poetry_executable(venv_path)
    python_path = _get_python_executable(venv_path)
    
    # Use poetry as a module if executable not found
    if not poetry_path.exists():
        cmd = [str(python_path), "-m", "poetry", "run"] + command.split()
    else:
        cmd = [str(poetry_path), "run"] + command.split()
    
    _info(f"Executing poetry run: {command}")
    return _run_command(cmd, cwd=project_root)


def _clean_venv(venv_path: Path) -> int:
    """Remove existing virtual environment."""
    if venv_path.exists():
        _info(f"Removing existing virtual environment at {venv_path}")
        try:
            shutil.rmtree(venv_path)
            return 0
        except Exception as e:
            _error(f"Failed to remove venv: {e}")
            return 1
    return 0


def _setup_environment(project_root: Path, clean: bool = False) -> int:
    """Setup the virtual environment and install dependencies."""
    venv_path = _get_venv_path(project_root)
    
    # Clean if requested
    if clean:
        rc = _clean_venv(venv_path)
        if rc != 0:
            return rc
    
    # Create venv if it doesn't exist
    if not _venv_exists(venv_path):
        rc = _create_venv(project_root, venv_path)
        if rc != 0:
            _error("Failed to create virtual environment")
            return rc
    else:
        _info(f"Virtual environment already exists at {venv_path}")
    
    # Install poetry if not installed
    if not _poetry_is_installed(venv_path):
        rc = _install_poetry(venv_path)
        if rc != 0:
            _error("Failed to install poetry")
            return rc
    else:
        _info("Poetry is already installed")
    
    # Install dependencies
    rc = _install_dependencies(project_root, venv_path)
    if rc != 0:
        _error("Failed to install dependencies")
        return rc
    
    _info("Setup completed successfully!")
    return 0


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup venv, install poetry, and run poetry commands"
    )
    parser.add_argument(
        "--command",
        default="probe --help",
        help="Poetry command to run (default: probe --help)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing venv and start fresh",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Only setup, don't run any command",
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Main entry point."""
    args = _parse_args(argv)
    
    # Get project root (directory containing this script)
    project_root = Path(__file__).parent.resolve()
    
    _info(f"Project root: {project_root}")
    
    # Setup environment
    rc = _setup_environment(project_root, clean=args.clean)
    if rc != 0:
        return rc
    
    # Run command if not --no-run
    if not args.no_run:
        venv_path = _get_venv_path(project_root)
        rc = _run_poetry_command(project_root, venv_path, args.command)
        return rc
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
