#!/bin/bash
# Load environment variables from .env file
# Usage: source scripts/setup-env.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.env" ]; then
    echo "🔑 Loading environment variables from .env..."
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | grep -v '^$' | xargs)
    echo "✅ Environment loaded!"
    echo ""
    echo "📋 Checking AWS credentials..."
    aws sts get-caller-identity
    echo ""
    echo "📍 Current AWS region: $AWS_REGION"
    echo "🔐 NGC API Key: ${NGC_API_KEY:0:20}..."
else
    echo "❌ .env file not found at $PROJECT_DIR/.env"
    exit 1
fi
