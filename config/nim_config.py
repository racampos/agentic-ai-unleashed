"""
NIM Configuration Module

Provides easy switching between NVIDIA hosted API (free for development)
and self-hosted NIM deployments (for production/demo).

Usage:
    from config.nim_config import get_llm_client, get_embedding_client

    # Get clients based on NIM_MODE environment variable
    llm_client = get_llm_client()
    embedding_client = get_embedding_client()

    # Or explicitly specify mode
    llm_client = get_llm_client(mode="hosted")
    llm_client = get_llm_client(mode="self-hosted")
"""

import os
from typing import Literal, Optional
from openai import OpenAI


def get_nim_mode() -> Literal["hosted", "self-hosted"]:
    """Get the current NIM deployment mode from environment variable."""
    mode = os.getenv("NIM_MODE", "hosted").lower()
    if mode not in ["hosted", "self-hosted"]:
        raise ValueError(f"Invalid NIM_MODE: {mode}. Must be 'hosted' or 'self-hosted'")
    return mode


def get_llm_config(mode: Optional[str] = None) -> dict:
    """
    Get LLM configuration based on deployment mode.

    Args:
        mode: Override NIM_MODE env var. Either "hosted" or "self-hosted"

    Returns:
        dict with 'base_url', 'api_key', and 'model' keys
    """
    mode = mode or get_nim_mode()

    if mode == "hosted":
        return {
            "base_url": os.getenv("NVIDIA_HOSTED_LLM_URL", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("NVIDIA_API_KEY"),
            "model": os.getenv("NVIDIA_LLM_MODEL", "nvidia/llama-3.1-nemotron-nano-8b-v1"),
        }
    else:  # self-hosted
        return {
            "base_url": os.getenv("SELF_HOSTED_LLM_URL", "http://llm-nim.nim.svc.cluster.local:8000/v1"),
            "api_key": os.getenv("NGC_API_KEY"),  # NGC key used for self-hosted NIM
            "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
        }


def get_embedding_config(mode: Optional[str] = None) -> dict:
    """
    Get embedding configuration based on deployment mode.

    Args:
        mode: Override NIM_MODE env var. Either "hosted" or "self-hosted"

    Returns:
        dict with 'base_url', 'api_key', and 'model' keys
    """
    mode = mode or get_nim_mode()

    if mode == "hosted":
        return {
            "base_url": os.getenv("NVIDIA_HOSTED_EMB_URL", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("NVIDIA_API_KEY"),
            "model": os.getenv("NVIDIA_EMB_MODEL", "nvidia/nv-embedqa-e5-v5"),
        }
    else:  # self-hosted
        return {
            "base_url": os.getenv("SELF_HOSTED_EMB_URL", "http://embed-nim.nim.svc.cluster.local:8000/v1"),
            "api_key": os.getenv("NGC_API_KEY"),  # NGC key used for self-hosted NIM
            "model": "nvidia/nv-embedqa-e5-v5",
        }


def get_llm_client(mode: Optional[str] = None) -> OpenAI:
    """
    Get an OpenAI-compatible client for LLM inference.

    Args:
        mode: Override NIM_MODE env var. Either "hosted" or "self-hosted"

    Returns:
        OpenAI client configured for the selected mode

    Example:
        >>> client = get_llm_client()
        >>> response = client.chat.completions.create(
        ...     model=get_llm_config()["model"],
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     max_tokens=100
        ... )
    """
    config = get_llm_config(mode)
    return OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"]
    )


def get_embedding_client(mode: Optional[str] = None) -> OpenAI:
    """
    Get an OpenAI-compatible client for embedding generation.

    Args:
        mode: Override NIM_MODE env var. Either "hosted" or "self-hosted"

    Returns:
        OpenAI client configured for the selected mode

    Example:
        >>> client = get_embedding_client()
        >>> response = client.embeddings.create(
        ...     model=get_embedding_config()["model"],
        ...     input=["Hello world"],
        ...     extra_body={"input_type": "query"}
        ... )
    """
    config = get_embedding_config(mode)
    return OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"]
    )


def print_config(mode: Optional[str] = None):
    """Print current configuration for debugging."""
    mode = mode or get_nim_mode()
    print(f"\n{'='*60}")
    print(f"NIM Configuration (Mode: {mode})")
    print(f"{'='*60}\n")

    llm_config = get_llm_config(mode)
    print("LLM Configuration:")
    print(f"  Base URL: {llm_config['base_url']}")
    print(f"  Model: {llm_config['model']}")
    print(f"  API Key: {'*' * (len(llm_config['api_key']) - 8) + llm_config['api_key'][-8:] if llm_config['api_key'] else 'NOT SET'}")

    print()

    emb_config = get_embedding_config(mode)
    print("Embedding Configuration:")
    print(f"  Base URL: {emb_config['base_url']}")
    print(f"  Model: {emb_config['model']}")
    print(f"  API Key: {'*' * (len(emb_config['api_key']) - 8) + emb_config['api_key'][-8:] if emb_config['api_key'] else 'NOT SET'}")

    print(f"\n{'='*60}\n")

    if mode == "hosted":
        print("💡 Using NVIDIA hosted API - FREE for development!")
        print("   No GPU costs during development")
    else:
        print("⚙️  Using self-hosted NIMs on EKS")
        print("   Cost: ~$3.85/hour when GPUs running")
        print("   Use ./scripts/stop-gpus.sh to save costs")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Test the configuration
    print_config()
