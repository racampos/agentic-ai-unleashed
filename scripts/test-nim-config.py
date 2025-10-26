#!/usr/bin/env python3
"""
Test script for NIM configuration

Tests both hosted and self-hosted modes to verify connectivity
and API functionality.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import config module
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.nim_config import (
    get_llm_client,
    get_embedding_client,
    get_llm_config,
    get_embedding_config,
    print_config
)


def test_llm(mode: str):
    """Test LLM inference"""
    print(f"\n{'='*60}")
    print(f"Testing LLM ({mode} mode)")
    print(f"{'='*60}\n")

    try:
        client = get_llm_client(mode)
        config = get_llm_config(mode)

        print(f"Making request to: {config['base_url']}")
        print(f"Model: {config['model']}\n")

        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "user", "content": "What is Kubernetes in one sentence?"}
            ],
            max_tokens=50,
            temperature=0.7
        )

        print("✅ LLM Response:")
        print(f"   {response.choices[0].message.content}\n")
        return True

    except Exception as e:
        print(f"❌ LLM Error: {e}\n")
        return False


def test_embedding(mode: str):
    """Test embedding generation"""
    print(f"\n{'='*60}")
    print(f"Testing Embedding ({mode} mode)")
    print(f"{'='*60}\n")

    try:
        client = get_embedding_client(mode)
        config = get_embedding_config(mode)

        print(f"Making request to: {config['base_url']}")
        print(f"Model: {config['model']}\n")

        # Both hosted and self-hosted need input_type for nv-embedqa-e5-v5
        response = client.embeddings.create(
            model=config["model"],
            input=["Kubernetes is a container orchestration platform"],
            extra_body={"input_type": "query"}
        )

        embedding = response.data[0].embedding
        print(f"✅ Embedding Response:")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}\n")
        return True

    except Exception as e:
        print(f"❌ Embedding Error: {e}\n")
        return False


def main():
    """Main test function"""
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # Get current mode from environment
    current_mode = os.getenv("NIM_MODE", "hosted")

    print("\n" + "="*60)
    print("NIM Configuration Test")
    print("="*60)

    # Print current configuration
    print_config()

    # Test current mode
    print(f"\nTesting current mode: {current_mode}")
    llm_success = test_llm(current_mode)
    emb_success = test_embedding(current_mode)

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Mode: {current_mode}")
    print(f"LLM: {'✅ PASS' if llm_success else '❌ FAIL'}")
    print(f"Embedding: {'✅ PASS' if emb_success else '❌ FAIL'}")
    print("="*60 + "\n")

    if current_mode == "hosted":
        print("💡 Tip: To test self-hosted mode:")
        print("   1. Make sure GPUs are running: ./scripts/start-gpus.sh")
        print("   2. Set NIM_MODE=self-hosted in .env")
        print("   3. Run this script again from within a pod in the cluster")
    else:
        print("💡 Tip: To test hosted mode:")
        print("   1. Set NIM_MODE=hosted in .env")
        print("   2. Run this script again")
        print("   3. Stop GPUs to save money: ./scripts/stop-gpus.sh")

    return 0 if (llm_success and emb_success) else 1


if __name__ == "__main__":
    sys.exit(main())
