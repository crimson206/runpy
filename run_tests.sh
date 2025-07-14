#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "test-venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv test-venv --without-pip
fi

# Install pip manually in the virtual environment
if [ ! -f "test-venv/bin/pip" ]; then
    echo "Installing pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | test-venv/bin/python3
fi

# Activate virtual environment
source test-venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e .
pip install pytest allure-pytest pyshell packaging gitpython

# Run tests
echo "Running tests..."
pytest -v "$@"