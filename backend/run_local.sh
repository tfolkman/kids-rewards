#!/bin/bash
# Run the backend server locally on port 3000

cd /home/aiden/Coding/kids-rewards/backend

# Check if uvicorn is installed globally
if ! command -v uvicorn &> /dev/null; then
    # If not, check for virtual environment
    if [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "Installing uvicorn..."
        pip install uvicorn
    fi
fi

# Run uvicorn on port 3000
echo "Starting backend server on http://localhost:3000"
echo "Press Ctrl+C to stop the server"
uvicorn main:app --reload --port 3000 --host 0.0.0.0