#!/bin/bash
# Test RAG retrieval

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Testing RAG Retrieval"
echo "========================================="

# Load environment variables
echo "Loading environment variables..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# Export Python path
export PYTHONPATH="$PROJECT_ROOT"

# Run retriever test
echo "Running RAG retriever test..."
python "$PROJECT_ROOT/orchestrator/rag_retriever.py"
