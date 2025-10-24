# AI Coach EKS Cluster - Deployment Guide

## Overview

This CDK project creates a production-ready EKS cluster for the AI Coach hackathon, including:

- **VPC**: 10.1.0.0/16 with public/private subnets across 2 AZs
- **EKS Cluster**: Kubernetes v1.32 with GPU support
- **CPU Node Group**: 2x t3.large (for system workloads and orchestrator)
- **GPU Node Group**: 0-3x g6.xlarge (NVIDIA L4 GPUs, starts at 0 for cost savings)
- **NVIDIA GPU Operator**: Automatically installed via Helm
- **Namespaces**: `nim` (for NVIDIA NIMs) and `orchestrator` (for LangGraph)
- **RBAC**: Service accounts and roles for secure deployments

**Cost-optimized design**: GPU nodes start at 0 and scale up when needed.

## Prerequisites

1. **AWS Credentials**: Ensure your AWS credentials are loaded:
   ```bash
   source scripts/setup-env.sh
   ```

2. **AWS CDK**: Already installed (v2.1031.0)

3. **Python Virtual Environment**: Already set up in `.venv/`

## Deployment Steps

### 1. Bootstrap CDK (First-Time Only)

If you haven't used CDK in this AWS account/region before:

```bash
cd infrastructure/ai-coach
source .venv/bin/activate
cdk bootstrap
```

This creates the necessary S3 buckets and IAM roles for CDK.

### 2. Deploy the EKS Cluster

```bash
cd infrastructure/ai-coach
source .venv/bin/activate
cdk deploy
```

**Timeline**: ~45-60 minutes
- VPC creation: ~2 minutes
- EKS cluster: ~15 minutes
- Node group: ~5 minutes
- GPU Operator: ~20-30 minutes (downloads NVIDIA drivers)

### 3. Configure kubectl

After deployment completes, CDK will output a command like:

```bash
aws eks update-kubeconfig --name ai-coach-cluster --region us-east-1
```

Run this command to configure kubectl to access your cluster.

### 4. Verify GPU Nodes

```bash
# Check node status
kubectl get nodes -o wide

# Verify GPU operator pods are running
kubectl get pods -n gpu-operator

# Check GPU resources
kubectl describe node | grep -A 5 "Allocatable"
```

You should see `nvidia.com/gpu: 1` under Allocatable resources.

### 5. Update NGC API Key Secret

Replace the placeholder NGC API key:

```bash
kubectl create secret generic ngc-api-key \
  --from-literal=NGC_API_KEY=$NGC_API_KEY \
  --dry-run=client -o yaml | kubectl apply -f - -n nim
```

### 6. Verify Namespaces

```bash
kubectl get namespaces
```

You should see:
- `nim` - for NVIDIA NIM deployments
- `orchestrator` - for LangGraph orchestrator
- `gpu-operator` - for NVIDIA GPU Operator

### 7. Scale Up GPU Nodes (When Ready for NIMs)

The cluster deploys with 0 GPU nodes to save costs. Scale up when ready to deploy NIMs:

```bash
# Scale GPU node group to 1
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-gpu-nodes \
  --scaling-config minSize=0,desiredSize=1,maxSize=3

# Wait for node to be ready (~5 minutes)
kubectl get nodes -w

# Verify GPU resources
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable."nvidia\.com/gpu"
```

**Important**: GPU Operator will start installing drivers when the first GPU node joins. This takes ~20-30 minutes. Monitor with:

```bash
kubectl get pods -n gpu-operator -w
```

Wait until all pods show `Running` or `Completed` before deploying NIMs.

## Cost Estimation

### Initial Deployment (CPU nodes only, GPU at 0)
**Hourly cost**: ~$0.50/hour
- EKS Control Plane: $0.10/hour
- NAT Gateway: ~$0.045/hour
- 2x t3.large: ~$0.166/hour ($0.0832 each)
- Data transfer: Variable (~$0.10/hour estimate)

**Daily cost**: ~$12/day
**With $100 budget**: ~8 days runtime

### Active Development (with 1 GPU node)
**Hourly cost**: ~$1.50/hour
- Above baseline: $0.50/hour
- 1x g6.xlarge: ~$1.006/hour

**Daily cost**: ~$36/day
**With $100 budget**: ~2.7 days runtime

### Cost-Saving Strategies

**During breaks (overnight, meals)**:
Scale GPU nodes to 0:
```bash
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-gpu-nodes \
  --scaling-config minSize=0,desiredSize=0,maxSize=3
```
**Savings**: ~$1/hour (~$24/day)

**Extended breaks (day off)**:
Scale CPU nodes to 1:
```bash
aws eks update-nodegroup-config \
  --cluster-name ai-coach-cluster \
  --nodegroup-name ai-coach-cpu-nodes \
  --scaling-config minSize=1,desiredSize=1,maxSize=3
```
**Additional savings**: ~$0.08/hour (~$2/day)

**Total idle cost**: ~$0.15/hour (just EKS + NAT)

### Budget Optimization Plan

With $100 budget for 1-week hackathon:
1. **Days 1-2**: CPU-only setup (~$24)
2. **Days 3-5**: Active development with GPU (~$108)
3. **Scale to 0 overnight**: Save ~$24/day
4. **Switch to personal account** when credits run low

## Teardown (When Done)

To delete all resources and stop charges:

```bash
cd infrastructure/ai-coach
source .venv/bin/activate
cdk destroy
```

**Important**: This will delete:
- All deployments in `nim` and `orchestrator` namespaces
- The EKS cluster
- The VPC and all networking resources

## Migration to Personal Account

When your $100 credits run out:

1. Update credentials in `.env`
2. Run `cdk bootstrap` in the new account
3. Run `cdk deploy` (uses same code)
4. Update `kubeconfig`
5. Redeploy NIM containers

Total time: ~15 minutes + deployment time

## Troubleshooting

### GPU Operator Not Running

```bash
# Check GPU operator logs
kubectl logs -n gpu-operator -l app=nvidia-gpu-operator

# Restart GPU operator if needed
kubectl rollout restart deployment gpu-operator -n gpu-operator
```

### Node Not Ready

```bash
# Check node status
kubectl describe node <node-name>

# Check kubelet logs (via AWS Systems Manager)
aws ssm start-session --target <instance-id>
```

### CDK Deploy Fails

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name AiCoachEksStack \
  --max-items 20

# Rollback and retry
cdk destroy
cdk deploy
```

## Next Steps

After the cluster is deployed:

1. **Phase 2**: Deploy Embedding NIM (nv-embedqa-e5-v5)
2. **Phase 2**: Build FAISS index from lesson content
3. **Phase 3**: Deploy LLM NIM (llama-3.1-nemotron-nano-8B-v1)
4. **Phase 4**: Deploy LangGraph orchestrator

See `IMPLEMENTATION_PLAN.md` for detailed phase breakdown.

## Stack Outputs

CDK automatically provides these outputs after deployment:

- `AiCoachEksStack.ClusterName` - Cluster name
- `AiCoachEksStack.ClusterArn` - Cluster ARN
- `AiCoachEksStack.ClusterEndpoint` - API server endpoint
- `AiCoachEksStack.ConfigCommand` - kubectl configuration command

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)
