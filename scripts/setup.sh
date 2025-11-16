#!/bin/bash
# Setup script for Alavista development environment

set -e

echo "Setting up Alavista development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11 or higher is required"
    exit 1
fi

echo "✓ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

echo "✓ Dependencies installed"

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
fi

# Create data directory
mkdir -p data

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Run tests: pytest"
echo "  3. Start development!"
