#!/bin/bash
# Start GPU nodes and wait for NIMs to be ready
# This will create g6.xlarge (embedding) and g6.2xlarge (LLM) instances

set -e

echo "========================================="
echo "Starting GPU Nodes"
echo "========================================="
echo ""

# Load AWS credentials from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "Scaling embedding GPU nodegroup (g6.xlarge) to 1..."
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-embedding-gpu-nodes \
  --scaling-config desiredSize=1,minSize=0,maxSize=2 \
  --region us-east-1

echo ""
echo "Scaling LLM GPU nodegroup (g6.4xlarge) to 1..."
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-llm-gpu-nodes \
  --scaling-config desiredSize=1,minSize=0,maxSize=2 \
  --region us-east-1

echo ""
echo "⏳ Waiting for GPU nodes to become ready (this takes ~3-5 minutes)..."
echo ""

# Wait for both nodes to be ready (timeout after 10 minutes)
if kubectl wait --for=condition=Ready nodes -l nvidia.com/gpu=true --timeout=10m 2>/dev/null; then
    echo ""
    echo "✅ GPU nodes are ready:"
    kubectl get nodes -l nim-type
    echo ""
    echo "Current pod status:"
    kubectl get pods -n nim
    echo ""
    echo "⏳ NIM initialization times:"
    echo "   - Embedding NIM: ~2-3 minutes"
    echo "   - LLM NIM: ~15-30 minutes (TensorRT engine building)"
    echo ""
    echo "Monitor with: kubectl get pods -n nim -w"
    echo ""
else
    echo ""
    echo "⚠️  Timeout waiting for nodes. Check status:"
    kubectl get nodes -l nvidia.com/gpu=true
    echo ""
    echo "You can monitor pods manually with:"
    echo "  kubectl get pods -n nim -w"
fi
