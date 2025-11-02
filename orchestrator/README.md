# AI Networking Lab Tutor - LangGraph Orchestrator

An intelligent tutoring system that guides students through networking lab exercises using a sophisticated dual-path LangGraph architecture, RAG (Retrieval-Augmented Generation), and NVIDIA NIMs.

## Architecture Overview

The system implements a **dual-path LangGraph workflow** that intelligently routes student questions to optimize for both learning and troubleshooting:

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

### The 6 Core Nodes

1. **intent_router_node** - Fast heuristic routing (~100ms) using keywords + CLI error detection
2. **teaching_retrieval_node** - Retrieves conceptual docs with query expansion (200-500ms)
3. **teaching_feedback_node** - Generates clear educational explanations (2-5s)
4. **retrieval_node** - Error-focused RAG retrieval with smart prioritization (300-700ms)
5. **feedback_node** - Complex multi-stage node with inline error detection, tool calling, and reasoning (5-15s)
6. **paraphrasing_node** - Cleans responses by removing preambles and internal references (1-3s)

### Smart Routing Logic

The **intent_router_node** automatically routes based on:

- **CLI errors detected** → troubleshooting path (high confidence)
- **Teaching keywords** (what, why, explain, how does) → teaching path
- **Troubleshooting keywords** (error, issue, not working) → troubleshooting path
- **Default**: Falls back to teaching path for ambiguous cases

### Key Integration Points

**Error Detection Framework**

- 100+ regex-based error patterns
- Fuzzy matching for typo detection (hostnane → hostname)
- Inline detection in feedback_node
- Proactive CLI error diagnosis (recent POC)

**Tool Calling**

- `get_device_running_config()` for context gathering
- Smart iteration (max 3 calls)
- Automatically disabled when CLI errors already visible

**RAG System**

- FAISS-based vector search with NVIDIA Embed NIM
- Error-aware document prioritization
- Query expansion for teaching path
- Lab-specific filtering

**Streaming Architecture**

- Phase-based content delivery
- Content filtering (removes internal markers)
- 2-3s time-to-first-token

## State Management

The `TutoringState` TypedDict (40+ fields) flows through the entire pipeline:

**Critical State Fields:**

- `cli_history` - Recent CLI commands/output (drives error detection and routing)
- `student_question` - Current question
- `conversation_history` - Full chat history
- `retrieved_context` - RAG results
- `intent` - Routing decision (teaching vs troubleshooting)
- `error_analysis` - Detected errors and diagnoses
- `response` - Generated tutor response

## Components

```
orchestrator/
├── README.md                    # This file
├── docs/                        # Detailed documentation
│   ├── ARCHITECTURE.md          # Complete system analysis (860 lines)
│   ├── QUICK_REFERENCE.md       # Developer reference (247 lines)
│   └── ARCHITECTURE_DIAGRAMS.txt # ASCII flow diagrams (309 lines)
├── __init__.py
├── state.py                     # TutoringState TypedDict definition
├── nodes.py                     # 6 LangGraph node implementations
├── graph.py                     # LangGraph workflow + routing logic
├── tutor.py                     # Main tutor interface
├── rag_indexer.py               # RAG indexing pipeline
├── rag_retriever.py             # RAG retrieval system
├── error_detection/             # Error pattern framework
│   ├── patterns.py              # Regex patterns + fuzzy matching
│   └── diagnoses.py             # Preprocessed diagnoses
└── paraphrasing/                # Response cleaning
    └── paraphraser.py           # Preamble removal agent
```

## Usage

### Starting a Lab Session

```python
from orchestrator.tutor import NetworkingLabTutor

# Create tutor instance
tutor = NetworkingLabTutor()

# Start a lab
welcome = tutor.start_lab("01-configure-initial-switch-settings", mastery_level="novice")
print(welcome["response"])

# Ask questions (automatically routed)
response = tutor.ask("What does the enable command do?")  # → teaching path
print(response["response"])

response = tutor.ask("I got an error: 'Invalid input detected'")  # → troubleshooting path
print(response["response"])
```

### Building the RAG Index

```bash
./scripts/build-rag-index.sh
```

This will:

- Load all `.md` files from `data/labs/`
- Chunk documents (512 tokens with 50 token overlap)
- Generate embeddings using NVIDIA Embed NIM
- Build FAISS index at `data/faiss_index/`

## Detailed Documentation

For comprehensive information, see:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete system analysis with implementation details
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Developer quick reference and testing guide
- **[ARCHITECTURE_DIAGRAMS.txt](docs/ARCHITECTURE_DIAGRAMS.txt)** - ASCII diagrams of all flows

## Configuration

The system uses dual-mode NIM configuration:

- **Hosted mode**: Free NVIDIA API for development (`NIM_MODE=hosted`)
- **Self-hosted mode**: Your own EKS deployment for production (`NIM_MODE=self-hosted`)

Set in `.env` file at project root.

## Dependencies

```bash
pip install langchain langchain-text-splitters langchain-core \
    langgraph faiss-cpu tiktoken openai python-dotenv
```

## License

This project is part of the Agentic AI Unleashed hackathon.
