# AI Networking Lab Tutor

A sophisticated multi-agent tutoring system that guides students through hands-on networking lab exercises using **LangGraph**, **RAG (Retrieval-Augmented Generation)**, and **NVIDIA NIMs**.

Built for the **Agentic AI Unleashed** hackathon.

## Overview

This project implements an intelligent AI tutor that provides a complete learning experience for networking students:
- Dual-path intelligent routing (teaching vs troubleshooting)
- Real-time CLI error detection with fuzzy matching
- Interactive guidance through networking labs (switching, routing, IPv4/IPv6)
- RAG-powered answers from lab documentation
- Tool-calling integration with NetGSim simulator
- Adaptive teaching based on student mastery level
- Streaming responses for real-time interaction

### Architecture

The system uses a **dual-path LangGraph architecture** that intelligently routes questions to optimize learning outcomes:

```
                    Student Question
                           ↓
                  intent_router_node
                    (fast routing)
                           ↓
         ┌─────────────────┴─────────────────┐
         │                                   │
   Teaching Path                    Troubleshooting Path
   (conceptual)                     (error diagnosis)
         │                                   │
         ↓                                   ↓
teaching_retrieval_node              retrieval_node
         ↓                                   ↓
teaching_feedback_node               feedback_node
         │                          (error detection +
         │                           tool calling)
         └─────────────────┬─────────────────┘
                           ↓
                  paraphrasing_node
                           ↓
                    Final Response
```

**Key Components:**
- **RAG System**: FAISS vector store with NVIDIA Embed NIM (1024-dim embeddings)
- **LLM NIM**: NVIDIA Llama models for reasoning and explanation
- **NetGSim**: Hosted network simulator for hands-on practice
- **Error Detection**: 100+ regex patterns with fuzzy matching for typo detection

For detailed architecture documentation, see [orchestrator/README.md](orchestrator/README.md).

## Features

### 1. Dual-Path LangGraph Orchestration
The system intelligently routes student questions through two optimized paths:

**Teaching Path** (Conceptual Learning):
- Query expansion for comprehensive documentation retrieval
- Educational explanations with clear context
- Socratic method for deeper understanding

**Troubleshooting Path** (Problem Solving):
- Inline CLI error detection with fuzzy matching (100+ patterns)
- Smart tool calling with `get_device_running_config()` (max 3 iterations)
- Error-aware RAG retrieval prioritizing relevant diagnostics
- Step-by-step debugging guidance

Both paths converge through a paraphrasing node that removes preambles and ensures concise responses.

### 2. Advanced Error Detection Framework
- **100+ regex-based patterns** covering common Cisco IOS errors
- **Fuzzy matching** for typo detection (e.g., "hostnane" → "hostname")
- **Proactive CLI analysis** from recent command history
- **Mode-aware detection** (user exec vs privileged exec vs config mode)
- Automatically disables tool calling when errors are already visible

### 3. RAG System with Smart Retrieval
- **FAISS vector store** with 1024-dimensional NVIDIA embeddings
- Automatic chunking (512 tokens, 50 token overlap)
- Lab-specific filtering and context prioritization
- Error-aware document ranking
- Query expansion for teaching scenarios

### 4. Tool Calling with NetGSim Integration
- **Smart iteration**: Automatically gathers device configs when needed
- **Context-aware**: Skips redundant calls when CLI history is sufficient
- **Result evaluation**: Analyzes configurations to provide accurate guidance
- Mirrors real-world microservices architecture

### 5. Adaptive Teaching
- **Novice**: Step-by-step guidance with detailed explanations
- **Intermediate**: Hints and conceptual questions to encourage thinking
- **Advanced**: Challenging extensions and self-exploration prompts

### 6. Streaming Architecture
- Phase-based content delivery (2-3s time-to-first-token)
- Content filtering removes internal markers
- Real-time user experience

## NetGSim Simulator

**NetGSim is a proprietary network simulator provided as a hosted service** - judges and developers do not need to deploy it.

- **Hosted at**: https://netgenius-production.up.railway.app
- **Architecture**: Microservices pattern (similar to using Stripe, Twilio, or other external APIs)
- **Purpose**: Provides realistic Cisco IOS CLI simulation for hands-on practice
- **Integration**: The tutor calls NetGSim APIs to execute commands and retrieve configurations

This mirrors real-world software architecture where applications integrate with external services rather than deploying everything in-house. The simulator handles device emulation, command execution, and state management while the tutor focuses on pedagogy and intelligent assistance.

## Quick Start

### System Components

1. **Frontend** (React + TypeScript + Vite)
   - Modern chat interface with streaming responses
   - Lab selection and mastery level configuration
   - Real-time CLI history display

2. **Backend API** (FastAPI)
   - RESTful endpoints for tutor interaction
   - WebSocket support for streaming
   - Session management and state persistence

3. **Orchestrator** (LangGraph)
   - Dual-path intelligent routing
   - RAG-powered retrieval
   - Error detection and tool calling

4. **NetGSim** (Hosted Service - No deployment needed)
   - Network device simulation
   - Cisco IOS CLI emulation

### Prerequisites

```bash
# Python 3.12+ for backend and orchestrator
pip install -r requirements.txt

# Node.js 18+ for frontend
cd frontend
npm install
```

### Environment Configuration

Create `.env` files in the project root and frontend directory:

**Root `.env`** (Backend + Orchestrator):
```bash
# NVIDIA NIM Configuration
NIM_MODE=hosted                           # or self-hosted
NVIDIA_API_KEY=your-nvidia-api-key       # Get free key at https://build.nvidia.com/

# NetGSim Simulator (Hosted Service)
SIMULATOR_BASE_URL=https://netgenius-production.up.railway.app

# Optional: Self-hosted NIM
# NGC_API_KEY=your-ngc-api-key
```

**Frontend `.env`**:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Running the Application

1. **Build RAG Index** (first time only):
```bash
./scripts/build-rag-index.sh
```

2. **Start Backend API**:
```bash
./start_backend.sh
# API runs on http://localhost:8000
```

3. **Start Frontend** (separate terminal):
```bash
cd frontend
npm run dev
# UI runs on http://localhost:5173
```

4. **Access the Application**:
   - Open browser to http://localhost:5173
   - Select a lab (Lab 01 or Lab 02)
   - Choose mastery level (Novice, Intermediate, Advanced)
   - Start learning!

## Project Structure

```
agentic-ai-unleashed/
├── README.md                           # This file
├── .env                                # Backend configuration (not in git)
├── requirements.txt                    # Python dependencies
├── start_backend.sh                    # Backend startup script
│
├── frontend/                           # React + TypeScript UI
│   ├── src/
│   │   ├── App.tsx                    # Main application component
│   │   ├── components/                # Reusable UI components
│   │   └── services/                  # API and WebSocket clients
│   ├── package.json                   # Node.js dependencies
│   ├── vite.config.ts                 # Vite configuration
│   └── .env                           # Frontend configuration
│
├── api/                                # FastAPI backend
│   └── main.py                        # REST + WebSocket endpoints
│
├── orchestrator/                       # LangGraph tutoring agent
│   ├── README.md                      # Detailed architecture docs
│   ├── docs/                          # Comprehensive documentation
│   │   ├── ARCHITECTURE.md            # Complete system analysis (860 lines)
│   │   ├── QUICK_REFERENCE.md         # Developer reference (247 lines)
│   │   └── ARCHITECTURE_DIAGRAMS.txt  # ASCII flow diagrams (309 lines)
│   ├── state.py                       # TutoringState TypedDict (40+ fields)
│   ├── nodes.py                       # 6 LangGraph node implementations
│   ├── graph.py                       # Dual-path workflow + routing
│   ├── tutor.py                       # Main tutor interface
│   ├── rag_indexer.py                 # RAG indexing pipeline
│   ├── rag_retriever.py               # RAG retrieval system
│   ├── error_detection/               # Error pattern framework
│   │   ├── patterns.py                # 100+ regex patterns + fuzzy matching
│   │   └── diagnoses.py               # Preprocessed diagnoses
│   └── paraphrasing/                  # Response cleaning
│       └── paraphraser.py             # Preamble removal agent
│
├── config/                             # NIM configuration
│   ├── README.md                      # NIM setup guide
│   └── nim_config.py                  # Dual-mode NIM client
│
├── data/                               # Lab content and indexes
│   ├── labs/                          # Lab documentation (markdown)
│   │   ├── 01-configure-initial-switch-settings.md
│   │   ├── 02-basic-device-configuration.md
│   │   ├── cisco-ios-command-reference.md
│   │   └── cisco-ios-error-patterns.md
│   └── faiss_index/                   # Vector store
│       ├── labs_index.faiss
│       └── labs_index_metadata.pkl
│
├── scripts/                            # Utility scripts
│   ├── build-rag-index.sh             # Build FAISS index
│   ├── test-rag-retrieval.sh          # Test RAG system
│   ├── test-tutor.sh                  # Test tutor
│   ├── test-nim-config.py             # Test NIM endpoints
│   ├── start-gpus.sh                  # Start EKS GPU nodes (self-hosted)
│   └── stop-gpus.sh                   # Stop GPU nodes (self-hosted)
│
├── infrastructure/                     # EKS deployment (optional, self-hosted)
│   └── ai-coach/                      # AWS CDK stack
│       └── ai_coach/
│           └── ai_coach_stack.py
│
└── kubernetes/                         # K8s manifests (optional, self-hosted)
    └── nim/
        ├── embedding-nim.yaml         # Embedding NIM deployment
        └── llm-nim.yaml               # LLM NIM deployment
```

## Lab Documentation

The system includes two hands-on networking labs:

### Lab 01: Configure Initial Switch Settings (Beginner)
**Duration**: ~20 minutes
**Topics**:
- Verify default switch configuration
- Configure hostname and passwords (plain text and encrypted)
- Secure console and privileged EXEC access
- Configure MOTD banners
- Save configurations to NVRAM
- Apply concepts to multiple switches

**Learning Outcomes**: Students learn fundamental Cisco IOS navigation, configuration modes, and security best practices.

### Lab 02: Basic Device Configuration (Intermediate)
**Duration**: ~45 minutes
**Topics**:
- Configure router and switch basic settings
- Set up IPv4 and IPv6 addresses on router interfaces
- Configure default gateways on PCs
- Verify end-to-end connectivity across multiple devices
- Troubleshoot configuration issues

**Prerequisites**: Completion of Lab 01
**Learning Outcomes**: Students gain experience with multi-device topologies, dual-stack networking (IPv4/IPv6), and systematic troubleshooting.

### Adding More Labs

To extend the system with additional labs:

1. Create a markdown file in `data/labs/` following the existing structure
2. Include frontmatter with metadata (id, title, difficulty, prerequisites)
3. Structure content with clear objectives, steps, and expected outcomes
4. Rebuild the RAG index: `./scripts/build-rag-index.sh`

The tutor will automatically incorporate new labs into its knowledge base.

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

### Frontend
- **React 18**: Modern UI framework with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **TailwindCSS**: Utility-first styling
- **React Markdown**: Rich text rendering

### Backend
- **FastAPI**: High-performance async Python web framework
- **WebSockets**: Real-time streaming communication
- **Pydantic**: Data validation and settings management
- **CORS middleware**: Cross-origin request handling

### Orchestration
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: Document processing and RAG utilities
- **FAISS**: High-performance vector similarity search
- **NVIDIA NIMs**: LLM inference and embeddings

### Infrastructure (Optional Self-Hosted)
- **AWS EKS**: Managed Kubernetes for GPU workloads
- **AWS CDK**: Infrastructure as code in Python
- **NVIDIA GPU**: L4 GPUs for NIM inference
- **Kubernetes**: Container orchestration

### External Services
- **NetGSim**: Proprietary network simulator (Railway hosted)
- **NVIDIA API**: Hosted NIM endpoints (free tier available)

## Environment Variables

### Backend Configuration (Root `.env`)

```bash
# NVIDIA NIM Configuration
NIM_MODE=hosted                           # Use 'hosted' for free NVIDIA API or 'self-hosted' for EKS
NVIDIA_API_KEY=nvapi-xxxxx               # Get free key at https://build.nvidia.com/

# NetGSim Simulator (Hosted Service)
SIMULATOR_BASE_URL=https://netgenius-production.up.railway.app

# Optional: Self-Hosted NIM Configuration
# NGC_API_KEY=your-ngc-api-key
# EMBED_NIM_URL=http://localhost:8001/v1
# LLM_NIM_URL=http://localhost:8000/v1
```

### Frontend Configuration (`frontend/.env`)

```bash
# Backend API URLs
VITE_API_BASE_URL=http://localhost:8000   # REST API endpoint
VITE_WS_BASE_URL=ws://localhost:8000      # WebSocket endpoint for streaming
```

### Configuration Notes

- **NIM_MODE**: Controls whether to use NVIDIA's free hosted API or your own self-hosted NIMs
  - `hosted`: Free tier, no infrastructure needed, great for development
  - `self-hosted`: Requires AWS EKS deployment, production-grade performance

- **SIMULATOR_BASE_URL**: Points to the hosted NetGSim service on Railway
  - No deployment needed - this is a managed service
  - Judges can use the application without deploying the simulator

- **API Keys**:
  - NVIDIA_API_KEY: Free tier available at https://build.nvidia.com/
  - NGC_API_KEY: Required only for self-hosted mode (download NIM containers)

## Development Roadmap

### Phase 1: Foundation ✅
- [x] EKS cluster setup (optional self-hosted mode)
- [x] NVIDIA GPU node pools
- [x] Embedding NIM deployment
- [x] FAISS indexing with 1024-dim embeddings
- [x] Dual-mode NIM configuration (hosted + self-hosted)
- [x] Cost management scripts

### Phase 2: LangGraph Orchestration ✅
- [x] Dual-path LangGraph architecture
- [x] Intent routing with heuristics
- [x] Teaching retrieval with query expansion
- [x] Troubleshooting retrieval with error prioritization
- [x] RAG system with semantic search
- [x] State management (40+ fields)
- [x] Paraphrasing node for response cleaning

### Phase 3: Error Detection & Tool Calling ✅
- [x] 100+ regex-based error patterns
- [x] Fuzzy matching for typo detection
- [x] Mode-aware error detection
- [x] Proactive CLI analysis from history
- [x] Smart tool calling with `get_device_running_config()`
- [x] Context-aware tool iteration (max 3 calls)
- [x] Automatic tool call disabling when errors visible

### Phase 4: Simulator Integration ✅
- [x] NetGSim API client integration
- [x] Device configuration retrieval
- [x] Command execution support
- [x] Result evaluation and analysis
- [x] Session state management
- [x] Hosted service architecture (Railway)

### Phase 5: Full-Stack Application ✅
- [x] FastAPI backend with REST + WebSocket
- [x] React + TypeScript frontend
- [x] Streaming response architecture
- [x] Real-time CLI history display
- [x] Lab selection and mastery level UI
- [x] Session persistence
- [x] Modern chat interface with Markdown support

### Phase 6: Polish & Optimization ✅
- [x] Response paraphrasing to remove preambles
- [x] Content filtering for clean user experience
- [x] Phase-based streaming (2-3s time-to-first-token)
- [x] Comprehensive documentation (ARCHITECTURE.md, QUICK_REFERENCE.md)
- [x] Testing framework for both paths
- [x] Error pattern generation tools

### Future Enhancements
- [ ] Multi-session lab progress tracking
- [ ] Student analytics dashboard
- [ ] Additional labs (VLANs, routing protocols, ACLs)
- [ ] Voice interface support
- [ ] Mobile responsive design improvements
- [ ] Admin panel for lab management

## Performance

### Response Latency (Hosted Mode)

- **Intent Routing**: ~100ms (keyword-based heuristics)
- **RAG Retrieval**:
  - Teaching path with query expansion: ~300-700ms
  - Troubleshooting path with error prioritization: ~200-500ms
- **LLM Generation**:
  - Teaching feedback: ~2-5s
  - Troubleshooting with tool calling: ~5-15s (includes device config retrieval)
- **Paraphrasing**: ~1-3s
- **Time-to-First-Token**: 2-3s (streaming architecture)
- **Total Response Time**:
  - Teaching path: ~3-8s
  - Troubleshooting path: ~6-18s (with tool calls)

### Self-Hosted Mode Performance

- **Embedding**: ~50ms per batch (32 texts) on g6.xlarge
- **LLM**: ~1-2s for 200 tokens on g6.4xlarge
- **Lower latency** due to dedicated GPU resources
- **Higher throughput** for concurrent requests

## Hackathon Highlights

This project was built for the **Agentic AI Unleashed** hackathon and demonstrates several advanced concepts:

### What Makes This Project Stand Out

1. **Sophisticated Multi-Agent Architecture**
   - Dual-path LangGraph design optimized for different learning scenarios
   - Intelligent routing based on intent classification
   - 6 specialized nodes working in concert

2. **Production-Ready Error Detection**
   - 100+ carefully crafted regex patterns
   - Fuzzy matching algorithm for typo tolerance
   - Proactive CLI analysis that catches errors before students ask

3. **Smart Tool Integration**
   - Context-aware tool calling that knows when to fetch device configs
   - Automatic iteration limiting to prevent redundant API calls
   - Mirrors real-world microservices patterns

4. **Real-World Architecture**
   - Full-stack application (React + FastAPI + LangGraph)
   - Streaming responses for better UX
   - External service integration (NetGSim on Railway)
   - Dual-mode deployment (free hosted + production self-hosted)

5. **Comprehensive Documentation**
   - 860+ lines of architecture documentation
   - ASCII diagrams showing all system flows
   - Developer quick reference guide

### Extending the Project

To add new labs:
1. Create markdown file in `data/labs/` following the existing structure
2. Include frontmatter with metadata (id, title, difficulty, etc.)
3. Rebuild the RAG index: `./scripts/build-rag-index.sh`
4. The tutor automatically incorporates new content

To add new error patterns:
1. Edit `orchestrator/error_detection/patterns.py`
2. Add regex pattern and diagnosis mapping
3. Test with the testing framework in root directory

## Testing

The project includes comprehensive testing for all major components:

### Integration Tests

```bash
# Build RAG index (required first time)
./scripts/build-rag-index.sh

# Test RAG retrieval system
./scripts/test-rag-retrieval.sh

# Test complete tutor workflow
./scripts/test-tutor.sh

# Test NIM configuration
python scripts/test-nim-config.py
```

### Unit Tests

```bash
# Test both teaching and troubleshooting paths
python test_both_paths.py

# Test intent classification and routing
python test_intent_classification.py

# Test fuzzy matching for error detection
python test_fuzzy_matching.py

# Test mode-aware fuzzy matching
python test_mode_aware_fuzzy.py

# Test teaching nodes specifically
python test_teaching_nodes.py

# Test streaming responses
python test_streaming.py
```

### Error Pattern Testing

```bash
# Test all error patterns against example outputs
python test_all_patterns.py

# Test specific pattern categories
python test_framework.py
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

- **NVIDIA** for free hosted NIM APIs, NGC containers, and L4 GPU infrastructure
- **LangChain/LangGraph** for powerful multi-agent orchestration and RAG utilities
- **AWS** for EKS managed Kubernetes and GPU instance types
- **Railway** for reliable hosting of the NetGSim simulator
- **Anthropic** for Claude and the Agentic AI Unleashed hackathon

## For Judges

### Quick Evaluation Guide

1. **Clone and Setup** (5 minutes):
   ```bash
   git clone <repository-url>
   cd agentic-ai-unleashed
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

2. **Configure Environment**:
   - Get free NVIDIA API key: https://build.nvidia.com/
   - Create root `.env` with `NIM_MODE=hosted` and your API key
   - Create `frontend/.env` with API URLs (see Environment Variables section)

3. **Build RAG Index**:
   ```bash
   ./scripts/build-rag-index.sh
   ```

4. **Run Application**:
   - Terminal 1: `./start_backend.sh`
   - Terminal 2: `cd frontend && npm run dev`
   - Browser: http://localhost:5173

5. **Test Key Features**:
   - Select "Lab 01" and "Novice" level
   - Ask: "What does the enable command do?" (teaching path)
   - Paste an error message (troubleshooting path with error detection)
   - Notice streaming responses and clean formatting

### Architecture Deep Dive

For a comprehensive understanding of the system:
- Main architecture: `orchestrator/README.md`
- Complete analysis: `orchestrator/docs/ARCHITECTURE.md` (860 lines)
- Flow diagrams: `orchestrator/docs/ARCHITECTURE_DIAGRAMS.txt`
- Quick reference: `orchestrator/docs/QUICK_REFERENCE.md`

### What to Look For

- Dual-path routing intelligence
- Error detection with fuzzy matching
- Smart tool calling that avoids redundant API calls
- Response paraphrasing for clean UX
- Streaming architecture with phase-based delivery
- Real-world microservices integration (NetGSim on Railway)
