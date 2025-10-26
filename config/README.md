# NIM Configuration - Dual Mode Setup

This configuration allows you to easily switch between NVIDIA hosted API (free for development) and self-hosted NIMs on EKS (for production/demo).

## Quick Start

### 1. Using NVIDIA Hosted API (FREE - Recommended for Development)

```bash
# Set mode in .env
NIM_MODE=hosted

# Stop GPU nodes to save money
./scripts/stop-gpus.sh

# Develop your application using free hosted API
python your_app.py
```

**Benefits:**
- ✅ FREE for development
- ✅ No infrastructure costs
- ✅ Instant availability
- ✅ No GPU management

**Limitations:**
- ⚠️ Internet connection required
- ⚠️ Rate limits may apply
- ⚠️ Data leaves your infrastructure

### 2. Using Self-Hosted NIMs (Production/Demo)

```bash
# Start GPU nodes (takes 3-5 minutes for nodes, 15-30 min for LLM NIM)
./scripts/start-gpus.sh

# Wait for pods to be ready
kubectl get pods -n nim -w

# Set mode in .env
NIM_MODE=self-hosted

# Use self-hosted NIMs
python your_app.py

# Stop GPUs when done to save money
./scripts/stop-gpus.sh
```

**Benefits:**
- ✅ Full data privacy
- ✅ Lower latency
- ✅ No rate limits
- ✅ Works offline (within cluster)

**Costs:**
- 💰 ~$3.85/hour when running
- 💰 ~$92/day if left running 24/7

## Usage in Python Code

### Simple Usage

```python
from config.nim_config import get_llm_client, get_llm_config, get_embedding_client, get_embedding_config

# Get clients (mode determined by NIM_MODE env var)
llm_client = get_llm_client()
embedding_client = get_embedding_client()

# Get model names
llm_config = get_llm_config()
emb_config = get_embedding_config()

# LLM inference
response = llm_client.chat.completions.create(
    model=llm_config["model"],
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100
)
print(response.choices[0].message.content)

# Embedding generation
response = embedding_client.embeddings.create(
    model=emb_config["model"],
    input=["Hello world"],
    extra_body={"input_type": "query"}
)
print(len(response.data[0].embedding))  # 1024
```

### Explicit Mode Override

```python
from config.nim_config import get_llm_client

# Force hosted mode (good for testing)
llm_client = get_llm_client(mode="hosted")

# Force self-hosted mode
llm_client = get_llm_client(mode="self-hosted")
```

### Debug Configuration

```python
from config.nim_config import print_config

# Print current configuration
print_config()

# Print specific mode configuration
print_config(mode="hosted")
print_config(mode="self-hosted")
```

## Testing

```bash
# Test current mode (set in .env)
python scripts/test-nim-config.py

# The script will test both LLM and Embedding endpoints
# and show you the results
```

## Environment Variables Reference

```bash
# ========================================
# Mode Selection
# ========================================
NIM_MODE=hosted                    # or "self-hosted"

# ========================================
# API Keys
# ========================================
NVIDIA_API_KEY=nvapi-xxx          # For hosted mode (from build.nvidia.com)
NGC_API_KEY=nvapi-xxx             # For self-hosted mode (NGC registry)

# ========================================
# Hosted Endpoints (NVIDIA's servers)
# ========================================
NVIDIA_HOSTED_LLM_URL=https://integrate.api.nvidia.com/v1
NVIDIA_HOSTED_EMB_URL=https://integrate.api.nvidia.com/v1
NVIDIA_LLM_MODEL=nvidia/llama-3.1-nemotron-nano-8b-v1
NVIDIA_EMB_MODEL=nvidia/nv-embedqa-e5-v5

# ========================================
# Self-Hosted Endpoints (Your EKS cluster)
# ========================================
SELF_HOSTED_LLM_URL=http://llm-nim.nim.svc.cluster.local:8000/v1
SELF_HOSTED_EMB_URL=http://embed-nim.nim.svc.cluster.local:8000/v1
```

## Cost Management Strategy for Hackathon

### During Development (90% of time)
```bash
# Use hosted mode - FREE
NIM_MODE=hosted
./scripts/stop-gpus.sh

# Costs: ~$0.15/hour (EKS + NAT + CPU node only)
```

### During Testing/Demo (10% of time)
```bash
# Use self-hosted mode
./scripts/start-gpus.sh
NIM_MODE=self-hosted

# Test your application
# ...

# Stop when done
./scripts/stop-gpus.sh

# Costs while running: ~$3.85/hour
```

### Estimated Hackathon Costs (7 days)
- **Development (6 days, 8h/day)**: 48h × $0.15 = $7.20
- **Testing/Demo (1 day, 8h)**: 8h × $3.85 = $30.80
- **Total**: ~$38/week

vs. leaving GPUs running 24/7: ~$650/week 💸

## Getting Your NVIDIA API Key

1. Visit [build.nvidia.com](https://build.nvidia.com)
2. Sign up for a free NVIDIA Developer account
3. Navigate to any model page (e.g., Llama 3.1 Nemotron Nano 8B)
4. Click "Get API Key" or check your profile settings
5. Copy the API key and add it to `.env` as `NVIDIA_API_KEY`

## Troubleshooting

### "Module not found" errors
```bash
pip install openai python-dotenv
```

### Connection timeout to self-hosted NIMs
```bash
# Make sure GPUs are running
kubectl get pods -n nim

# Make sure you're running from within cluster or have port-forward set up
kubectl port-forward -n nim svc/llm-nim 8000:8000
```

### API authentication errors
```bash
# Check your API keys are set correctly
cat .env | grep API_KEY

# Make sure you're using the right key for the mode
# - NVIDIA_API_KEY for hosted mode
# - NGC_API_KEY for self-hosted mode
```

## API Compatibility

Both modes use OpenAI-compatible APIs, so your code works the same way regardless of mode!

```python
# This code works in BOTH modes without changes
response = llm_client.chat.completions.create(...)
```
