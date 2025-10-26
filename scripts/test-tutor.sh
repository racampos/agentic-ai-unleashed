#!/bin/bash
# Test the AI Networking Lab Tutor

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Testing AI Networking Lab Tutor"
echo "========================================="

# Load environment variables
echo "Loading environment variables..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# Export Python path
export PYTHONPATH="$PROJECT_ROOT"

# Run tutor demo
echo "Running tutor demo..."
python "$PROJECT_ROOT/orchestrator/tutor.py"
