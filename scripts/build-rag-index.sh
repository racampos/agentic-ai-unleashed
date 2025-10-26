#!/bin/bash
# Build RAG index from lab documentation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Building RAG Index"
echo "========================================="

# Load environment variables
echo "Loading environment variables..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# Export Python path
export PYTHONPATH="$PROJECT_ROOT"

# Run indexer
echo "Running RAG indexer..."
python "$PROJECT_ROOT/orchestrator/rag_indexer.py"

echo ""
echo "========================================="
echo "Index built successfully!"
echo "========================================="
