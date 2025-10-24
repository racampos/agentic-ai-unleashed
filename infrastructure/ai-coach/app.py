#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ai_coach.ai_coach_stack import AiCoachStack


app = cdk.App()

# Load environment from AWS credentials
# These should be set via the setup-env.sh script
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT', os.getenv('AWS_ACCOUNT_ID')),
    region=os.getenv('CDK_DEFAULT_REGION', os.getenv('AWS_REGION', 'us-east-1'))
)

AiCoachStack(
    app,
    "AiCoachEksStack",
    env=env,
    description="AI Coach EKS Cluster with GPU nodes for NVIDIA NIMs (Hackathon Infrastructure)",
)

app.synth()
