#!/bin/bash
# Run a Python test with environment variables loaded from .env

# Check if test file argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/run-test.sh <test_file.py>"
    echo "Example: ./scripts/run-test.sh tests/unit/test_teaching_nodes.py"
    exit 1
fi

# Load environment variables from .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Run the test
python "$@"
