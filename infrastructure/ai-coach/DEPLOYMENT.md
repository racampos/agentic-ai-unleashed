# AI Coach EKS Cluster - Deployment Guide

## Overview

This CDK project creates a production-ready EKS cluster for the AI Coach hackathon, including:

- **VPC**: 10.1.0.0/16 with public/private subnets across 2 AZs
- **EKS Cluster**: Kubernetes v1.32 with GPU support
- **GPU Node Group**: g6.xlarge instances (NVIDIA L4 GPUs)
- **NVIDIA GPU Operator**: Automatically installed via Helm
- **Namespaces**: `nim` (for NVIDIA NIMs) and `orchestrator` (for LangGraph)
- **RBAC**: Service accounts and roles for secure deployments

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

## Cost Estimation

**Estimated hourly cost**: ~$1.50/hour

Breakdown:
- NAT Gateway: ~$0.045/hour
- EKS Control Plane: $0.10/hour
- g6.xlarge (1 node): ~$1.006/hour (on-demand)
- Data transfer: Variable

**Daily cost**: ~$36/day
**Weekly cost**: ~$252/week

**Important**: With your $100 budget, you'll have ~2.5 days of runtime. Plan to:
1. Tear down when not actively working
2. Migrate to personal account mid-hackathon

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
