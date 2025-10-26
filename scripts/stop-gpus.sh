#!/bin/bash
# Stop GPU nodes to save costs when not working
# This will terminate both g6.xlarge (embedding) and g6.2xlarge (LLM) instances

set -e

echo "========================================="
echo "Stopping GPU Nodes"
echo "========================================="
echo ""

# Load AWS credentials from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "Scaling embedding GPU nodegroup (g6.xlarge) to 0..."
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-embedding-gpu-nodes \
  --scaling-config desiredSize=0,minSize=0,maxSize=2 \
  --region us-east-1

echo ""
echo "Scaling LLM GPU nodegroup (g6.4xlarge) to 0..."
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-llm-gpu-nodes \
  --scaling-config desiredSize=0,minSize=0,maxSize=2 \
  --region us-east-1

echo ""
echo "✅ Both GPU nodegroups scaled to 0"
echo ""
echo "Waiting for nodes to terminate..."
sleep 10
echo ""
echo "Current status:"
kubectl get nodes -l nvidia.com/gpu=true 2>/dev/null || echo "No GPU nodes running"
echo ""
echo "NIM pods will go to Pending state:"
kubectl get pods -n nim
echo ""
echo "💰 Cost savings: ~$3.85/hour (~$62/day)"
echo "   - g6.xlarge (embedding): $0.77/hour"
echo "   - g6.4xlarge (LLM): $3.08/hour"
echo ""
echo "To restart GPU nodes when you resume work, run:"
echo "  ./scripts/start-gpus.sh"
echo ""
echo "Note: LLM NIM will need 15-30 min to initialize after restart"
echo ""
