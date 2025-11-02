#!/bin/bash
# Script to start the backend server on port 8000

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

# Start the backend server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
