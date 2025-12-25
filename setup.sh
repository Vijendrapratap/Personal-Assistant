#!/bin/bash
set -e

echo "Initializing Alfred Environment..."

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate
source venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    echo "OPENAI_API_KEY=your_key_here" >> .env
    echo "DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/alfred_memory" >> .env
    echo "ALFRED_MODEL_TYPE=OPENAI" >> .env
fi

echo "Setup Complete!"
echo "Run 'source venv/bin/activate' to enter the environment."
echo "Then start the server with: 'python -m uvicorn alfred.main:app --reload'"
