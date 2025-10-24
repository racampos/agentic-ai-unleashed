from aws_cdk import (
    Stack,
    Tags,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from aws_cdk.lambda_layer_kubectl_v32 import KubectlV32Layer
from constructs import Construct


class AiCoachStack(Stack):
    """
    CDK Stack for AI Coach EKS Cluster with GPU nodes for NVIDIA NIMs.

    This stack creates:
    - VPC with public and private subnets across 2 AZs
    - EKS cluster (v1.32)
    - GPU node group (g6.xlarge for NVIDIA L4 GPUs)
    - NVIDIA GPU Operator via Helm
    - RBAC configuration for NIM deployments
    - Service accounts and IAM roles
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================
        # VPC Configuration
        # ========================================
        vpc = ec2.Vpc(
            self,
            "AiCoachVpc",
            vpc_name="ai-coach-vpc",
            max_azs=2,  # Use 2 AZs for high availability
            nat_gateways=1,  # Single NAT Gateway to save costs
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Tag VPC for cost tracking
        Tags.of(vpc).add("Project", "AI-Coach-Hackathon")
        Tags.of(vpc).add("ManagedBy", "CDK")

        # ========================================
        # EKS Cluster
        # ========================================

        # Create IAM role for EKS cluster
        cluster_role = iam.Role(
            self,
            "AiCoachClusterRole",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSVPCResourceController"),
            ],
        )

        # Create kubectl Lambda layer for EKS operations
        kubectl_layer = KubectlV32Layer(self, "KubectlLayer")

        # Create EKS cluster
        cluster = eks.Cluster(
            self,
            "AiCoachCluster",
            cluster_name="ai-coach-cluster",
            version=eks.KubernetesVersion.V1_32,
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            default_capacity=0,  # We'll add custom node groups
            role=cluster_role,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            kubectl_layer=kubectl_layer,
            # Enable cluster logging for troubleshooting
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
            ],
        )

        Tags.of(cluster).add("Project", "AI-Coach-Hackathon")
        Tags.of(cluster).add("ManagedBy", "CDK")

        # ========================================
        # GPU Node Group (g6.xlarge with NVIDIA L4)
        # ========================================

        # Create IAM role for GPU nodes
        gpu_node_role = iam.Role(
            self,
            "AiCoachGpuNodeRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),  # For Systems Manager access
            ],
        )

        # Add GPU node group
        gpu_nodegroup = cluster.add_nodegroup_capacity(
            "GpuNodeGroup",
            nodegroup_name="ai-coach-gpu-nodes",
            instance_types=[ec2.InstanceType("g6.xlarge")],  # NVIDIA L4 GPU
            min_size=1,
            max_size=3,
            desired_size=1,
            disk_size=100,  # 100GB for container images and NVIDIA drivers
            node_role=gpu_node_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            labels={
                "workload": "gpu",
                "nvidia.com/gpu": "true",
            },
            taints=[
                eks.TaintSpec(
                    key="nvidia.com/gpu",
                    value="true",
                    effect=eks.TaintEffect.NO_SCHEDULE,
                ),
            ],
        )

        Tags.of(gpu_nodegroup).add("Project", "AI-Coach-Hackathon")
        Tags.of(gpu_nodegroup).add("ManagedBy", "CDK")

        # ========================================
        # NVIDIA GPU Operator (via Helm)
        # ========================================

        # Add NVIDIA GPU Operator Helm chart
        gpu_operator = cluster.add_helm_chart(
            "NvidiaGpuOperator",
            chart="gpu-operator",
            repository="https://helm.ngc.nvidia.com/nvidia",
            namespace="gpu-operator",
            create_namespace=True,
            values={
                "operator": {
                    "defaultRuntime": "containerd",
                },
                "driver": {
                    "enabled": True,
                    "version": "550.90.07",  # Latest stable NVIDIA driver
                },
                "toolkit": {
                    "enabled": True,
                },
                "devicePlugin": {
                    "enabled": True,
                },
                "dcgm": {
                    "enabled": True,  # GPU metrics monitoring
                },
                "dcgmExporter": {
                    "enabled": True,  # Prometheus metrics
                },
                "gfd": {
                    "enabled": True,  # GPU Feature Discovery
                },
                "migManager": {
                    "enabled": False,  # Not needed for L4 GPUs
                },
                "nodeStatusExporter": {
                    "enabled": True,
                },
            },
        )

        # Ensure GPU operator is installed after node group
        gpu_operator.node.add_dependency(gpu_nodegroup)

        # ========================================
        # Namespaces for NIM deployments
        # ========================================

        # Create 'nim' namespace for NIM deployments
        nim_namespace = cluster.add_manifest(
            "NimNamespace",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": "nim",
                    "labels": {
                        "name": "nim",
                        "project": "ai-coach",
                    },
                },
            },
        )

        # Create 'orchestrator' namespace for LangGraph orchestrator
        orchestrator_namespace = cluster.add_manifest(
            "OrchestratorNamespace",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": "orchestrator",
                    "labels": {
                        "name": "orchestrator",
                        "project": "ai-coach",
                    },
                },
            },
        )

        # ========================================
        # Service Account for NIM deployments
        # ========================================

        # Create service account with necessary permissions
        nim_service_account = cluster.add_service_account(
            "NimServiceAccount",
            name="nim-deployer",
            namespace="nim",
        )

        # Ensure service account is created after namespace
        nim_service_account.node.add_dependency(nim_namespace)

        # Add RBAC for NIM service account
        nim_role = cluster.add_manifest(
            "NimRole",
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {
                    "name": "nim-deployer-role",
                    "namespace": "nim",
                },
                "rules": [
                    {
                        "apiGroups": [""],
                        "resources": ["pods", "services", "configmaps", "secrets"],
                        "verbs": ["get", "list", "watch", "create", "update", "patch", "delete"],
                    },
                    {
                        "apiGroups": ["apps"],
                        "resources": ["deployments", "statefulsets"],
                        "verbs": ["get", "list", "watch", "create", "update", "patch", "delete"],
                    },
                ],
            },
        )

        nim_role_binding = cluster.add_manifest(
            "NimRoleBinding",
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "RoleBinding",
                "metadata": {
                    "name": "nim-deployer-binding",
                    "namespace": "nim",
                },
                "roleRef": {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Role",
                    "name": "nim-deployer-role",
                },
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": "nim-deployer",
                        "namespace": "nim",
                    },
                ],
            },
        )

        # Ensure RBAC is created after service account
        nim_role.node.add_dependency(nim_service_account)
        nim_role_binding.node.add_dependency(nim_role)

        # ========================================
        # NGC API Key Secret (placeholder)
        # ========================================
        # Note: Actual secret value should be added after deployment
        # kubectl create secret generic ngc-api-key \
        #   --from-literal=NGC_API_KEY=$NGC_API_KEY \
        #   -n nim

        ngc_secret_placeholder = cluster.add_manifest(
            "NgcSecretPlaceholder",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "ngc-api-key",
                    "namespace": "nim",
                },
                "type": "Opaque",
                "stringData": {
                    "NGC_API_KEY": "PLACEHOLDER-UPDATE-AFTER-DEPLOYMENT",
                },
            },
        )

        ngc_secret_placeholder.node.add_dependency(nim_namespace)

        # ========================================
        # Outputs
        # ========================================
        # These are automatically available after cdk deploy

        # Note: CDK automatically outputs:
        # - Cluster name
        # - Cluster ARN
        # - Cluster endpoint
        # - kubectl configuration command
