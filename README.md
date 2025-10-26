# AI Networking Lab Tutor

An intelligent tutoring system that guides students through hands-on networking lab exercises using **LangGraph**, **RAG (Retrieval-Augmented Generation)**, and **NVIDIA NIMs**.

Built for the **Agentic AI Unleashed** hackathon.

## Overview

This project implements an AI-powered tutor that:
- Guides students through networking labs (routing, switching, VLANs, etc.)
- Answers questions using RAG on lab documentation
- Executes commands on a network simulator (NetGSim)
- Adapts teaching style based on student mastery level
- Provides personalized, contextual feedback

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Tutoring State Machine                    │   │
│  │                                                       │   │
│  │  Understanding → Retrieval → Planning → Feedback    │   │
│  │        ↓                                              │   │
│  │  Execution → Evaluation ─────────────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
└──────┬────────────────┬────────────────┬───────────────────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   RAG       │  │  LLM NIM    │  │  NetGSim    │
│  System     │  │  (Llama)    │  │ Simulator   │
│             │  │             │  │             │
│ - FAISS     │  │ - Reasoning │  │ - Execute   │
│ - Embed NIM │  │ - Explain   │  │ - Verify    │
│ - Docs      │  │ - Adapt     │  │ - Feedback  │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Features

### 1. Multi-Agent Tutoring System (LangGraph)
- **Understanding Agent**: Classifies student intent
- **Retrieval Agent**: Fetches relevant documentation
- **Planning Agent**: Chooses tutoring strategy
- **Execution Agent**: Runs commands on simulator
- **Evaluation Agent**: Assesses student progress
- **Feedback Agent**: Generates personalized responses

### 2. RAG System
- FAISS vector store with 1024-dim embeddings
- Automatic chunking and indexing of lab documentation
- Semantic search for relevant context
- Lab-specific filtering

### 3. Adaptive Teaching
- **Novice**: Step-by-step guidance, Socratic method
- **Intermediate**: Hints and conceptual questions
- **Advanced**: Challenging extensions, self-exploration

### 4. Dual-Mode NIM Deployment
- **Hosted Mode**: Free NVIDIA API for development
- **Self-Hosted Mode**: EKS deployment for production

## Quick Start

### Prerequisites

```bash
# Python dependencies
pip install langchain langchain-text-splitters langchain-core \
    langgraph faiss-cpu tiktoken openai python-dotenv

# AWS CLI (for self-hosted mode)
brew install awscli

# kubectl (for self-hosted mode)
brew install kubectl
```

### 1. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Development: Use hosted NIMs (FREE)
NIM_MODE=hosted
NVIDIA_API_KEY=your-nvidia-api-key

# Production: Use self-hosted NIMs
NIM_MODE=self-hosted
NGC_API_KEY=your-ngc-api-key
```

Get your free NVIDIA API key: https://build.nvidia.com/

### 2. Build RAG Index

Index the lab documentation:

```bash
./scripts/build-rag-index.sh
```

### 3. Run the Tutor

```bash
./scripts/test-tutor.sh
```

Or use programmatically:

```python
from orchestrator.tutor import NetworkingLabTutor

tutor = NetworkingLabTutor()
tutor.start_lab("01-basic-routing", mastery_level="novice")
response = tutor.ask("How do I configure an IP address?")
print(response["response"])
```

## Project Structure

```
agentic-ai-unleashed/
├── README.md                    # This file
├── .env                         # Configuration (not in git)
│
├── orchestrator/                # LangGraph tutoring agent
│   ├── README.md               # Orchestrator documentation
│   ├── architecture.md         # Detailed design
│   ├── state.py                # State definitions
│   ├── nodes.py                # LangGraph nodes
│   ├── graph.py                # Workflow definition
│   ├── tutor.py                # Main interface
│   ├── rag_indexer.py          # RAG indexing
│   └── rag_retriever.py        # RAG retrieval
│
├── config/                      # NIM configuration
│   ├── README.md               # NIM setup guide
│   └── nim_config.py           # Dual-mode NIM client
│
├── data/                        # Lab content and indexes
│   ├── labs/                   # Lab documentation
│   │   ├── 01-basic-routing.md
│   │   └── 02-static-routing.md
│   └── faiss_index/            # Vector store
│       ├── labs_index.faiss
│       └── labs_index_metadata.pkl
│
├── scripts/                     # Utility scripts
│   ├── build-rag-index.sh      # Build FAISS index
│   ├── test-rag-retrieval.sh   # Test RAG system
│   ├── test-tutor.sh           # Test tutor
│   ├── test-nim-config.py      # Test NIM endpoints
│   ├── start-gpus.sh           # Start EKS GPU nodes
│   └── stop-gpus.sh            # Stop GPU nodes
│
├── infrastructure/              # EKS deployment (self-hosted)
│   └── ai-coach/               # AWS CDK stack
│       └── ai_coach/
│           └── ai_coach_stack.py
│
└── kubernetes/                  # K8s manifests
    └── nim/
        ├── embedding-nim.yaml  # Embedding NIM deployment
        └── llm-nim.yaml        # LLM NIM deployment
```

## Lab Documentation

The system includes two sample labs:

### Lab 1: Basic Router Configuration
- Access router and enter privileged mode
- Configure hostname and passwords
- Configure IP addresses on interfaces
- Verify interface status
- Test connectivity with ping

### Lab 2: Static Routing Configuration
- Understand routing fundamentals
- Configure static routes
- Verify routing table entries
- Test end-to-end connectivity
- Configure default routes

Add more labs by creating markdown files in `data/labs/` and rebuilding the index.

## Deployment Modes

### Development (Hosted NIMs)

**Cost**: $0/month (FREE)

Uses NVIDIA's hosted API endpoints:
- LLM: `nvidia/llama-3.1-nemotron-nano-8b-v1`
- Embeddings: `nvidia/nv-embedqa-e5-v5`

Set `NIM_MODE=hosted` in `.env`.

### Production (Self-Hosted NIMs)

**Cost**: ~$3.85/hour when running (~$62/day)

Deploys to AWS EKS with GPU nodes:
- **Embedding NIM**: g6.xlarge (16GB RAM, 1x L4 GPU)
- **LLM NIM**: g6.4xlarge (64GB RAM, 1x L4 GPU)

#### Deploy Infrastructure

```bash
cd infrastructure/ai-coach
npm install
source .venv/bin/activate
cdk deploy
```

#### Configure kubectl

```bash
aws eks update-kubeconfig \
  --name ai-coach-cluster \
  --region us-east-1
```

#### Deploy NIMs

```bash
# Create NGC secret
kubectl create namespace nim
kubectl create secret generic ngc-api-key \
  -n nim \
  --from-literal=NGC_API_KEY=your-ngc-api-key

# Deploy NIMs
kubectl apply -f kubernetes/nim/embedding-nim.yaml
kubectl apply -f kubernetes/nim/llm-nim.yaml

# Wait ~3 minutes for embedding, ~20 minutes for LLM
kubectl get pods -n nim -w
```

#### Cost Management

Stop GPU nodes when not working:

```bash
# Stop nodes (saves ~$3.85/hour)
./scripts/stop-gpus.sh

# Start nodes when ready to work
./scripts/start-gpus.sh
```

## Technology Stack

- **LangGraph**: Multi-agent orchestration
- **LangChain**: Document processing and RAG utilities
- **FAISS**: Vector similarity search
- **NVIDIA NIMs**: LLM inference and embeddings
- **AWS EKS**: Kubernetes cluster for self-hosted NIMs
- **AWS CDK**: Infrastructure as code
- **Python**: 3.12+

## Development Roadmap

### Phase 1: Foundation ✅
- [x] EKS cluster setup
- [x] NVIDIA GPU node pools
- [x] Embedding NIM deployment
- [x] FAISS indexing

### Phase 2: LLM Integration ✅
- [x] LLM NIM deployment (g6.4xlarge)
- [x] Dual-mode NIM configuration
- [x] Cost management scripts

### Phase 3: Orchestration ✅
- [x] LangGraph state machine
- [x] RAG retrieval system
- [x] Tutoring nodes
- [x] Basic tutoring workflow

### Phase 4: Simulator Integration 🚧
- [ ] NetGSim API client
- [ ] Command parsing and execution
- [ ] Result evaluation

### Phase 5: Enhancement 📋
- [ ] Multi-turn conversation improvements
- [ ] Lab progress persistence
- [ ] Performance analytics
- [ ] Web UI

## Performance

- **RAG Retrieval**: ~200-500ms per query
- **LLM Generation**: ~1-3s per response
- **Total Response Time**: ~2-4s per interaction

With self-hosted NIMs:
- **Embedding**: ~50ms per batch (32 texts)
- **LLM**: ~1-2s for 200 tokens

## Contributing

This project was built for the Agentic AI Unleashed hackathon.

To add new labs:
1. Create markdown file in `data/labs/`
2. Follow existing lab structure
3. Run `./scripts/build-rag-index.sh`

## Testing

Run the complete test suite:

```bash
# Build index
./scripts/build-rag-index.sh

# Test retrieval
./scripts/test-rag-retrieval.sh

# Test tutor
./scripts/test-tutor.sh

# Test NIM configuration
python scripts/test-nim-config.py
```

## Troubleshooting

### RAG Index Issues

```bash
# Rebuild index
rm -rf data/faiss_index
./scripts/build-rag-index.sh
```

### NIM Connection Issues

```bash
# Test hosted mode
NIM_MODE=hosted python scripts/test-nim-config.py

# Test self-hosted mode
NIM_MODE=self-hosted python scripts/test-nim-config.py
```

### EKS Deployment Issues

```bash
# Check pod status
kubectl get pods -n nim

# View logs
kubectl logs -n nim -l app=embed-nim
kubectl logs -n nim -l app=llm-nim

# Check nodes
kubectl get nodes -l nvidia.com/gpu=true
```

## License

This project is part of the Agentic AI Unleashed hackathon.

## Acknowledgments

- **NVIDIA** for hosted NIMs and NGC containers
- **LangChain** for RAG utilities and orchestration
- **AWS** for EKS and GPU infrastructure

## Contact

For questions or issues, please open a GitHub issue.
