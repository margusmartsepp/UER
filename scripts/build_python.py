#!/usr/bin/env python3
"""Build script to prepare Python source for npm package distribution."""

import shutil
import sys
from pathlib import Path


def build() -> int:
    """Copy Python source to distribution directory."""
    print("Building UER MCP Python package...")

    # Define paths
    root = Path(__file__).parent.parent
    src = root / "src"
    python_dist = root / "python"

    # Clean previous build
    if python_dist.exists():
        print(f"Cleaning previous build: {python_dist}")
        shutil.rmtree(python_dist)

    # Create python distribution directory
    python_dist.mkdir(parents=True, exist_ok=True)

    # Copy source code (excluding __pycache__ and other build artifacts)
    print(f"Copying source from {src} to {python_dist / 'src'}")
    shutil.copytree(
        src,
        python_dist / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.pyd", ".pytest_cache"),
    )

    # Copy dependency files
    print("Copying dependency files...")
    shutil.copy(root / "pyproject.toml", python_dist / "pyproject.toml")

    if (root / "uv.lock").exists():
        shutil.copy(root / "uv.lock", python_dist / "uv.lock")

    # Copy README for reference
    if (root / "README.md").exists():
        shutil.copy(root / "README.md", python_dist / "README.md")

    print("✓ Build complete!")
    print(f"  Python package ready at: {python_dist}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(build())
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
