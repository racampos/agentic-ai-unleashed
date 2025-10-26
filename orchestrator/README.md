# AI Networking Lab Tutor - LangGraph Orchestrator

An intelligent tutoring system that guides students through networking lab exercises using LangGraph, RAG (Retrieval-Augmented Generation), and NVIDIA NIMs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Tutoring State Machine                    │   │
│  │  1. Understanding → 2. Retrieval → 3. Planning      │   │
│  │       ↓                  ↓             ↓             │   │
│  │  4. Execution → 5. Evaluation → 6. Feedback         │   │
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

## Components

### 1. State Management (`state.py`)

Defines the complete state for tutoring conversations:
- **Student Interaction**: Questions, conversation history
- **Lab Context**: Current lab, step, objectives
- **Retrieved Context**: Relevant documentation from RAG
- **Command Execution**: Commands and results from simulator
- **Tutoring Logic**: Strategy, feedback, hints
- **Student Progress**: Mastery level, success rate

### 2. RAG System

#### Indexing (`rag_indexer.py`)
- Loads lab documentation from `data/labs/`
- Chunks documents (512 tokens with 50 token overlap)
- Generates embeddings using NVIDIA Embed NIM
- Builds FAISS index for fast similarity search

#### Retrieval (`rag_retriever.py`)
- Query FAISS index with student questions
- Retrieve top-k most relevant documentation chunks
- Filter by lab if needed
- Return context for LLM generation

### 3. LangGraph Nodes (`nodes.py`)

Six specialized nodes for the tutoring workflow:

1. **Understanding Node**
   - Parse student input
   - Identify intent: question, command, help, next_step
   - Route to appropriate next node

2. **Retrieval Node**
   - Query FAISS with student question
   - Retrieve relevant lab documentation
   - Extract concepts and examples

3. **Planning Node**
   - Determine tutoring strategy based on mastery level
   - Choose approach: socratic, direct, hint, challenge
   - Adapt to student's needs

4. **Execution Node** (TODO: NetGSim integration)
   - Parse commands from student input
   - Execute on network simulator
   - Capture output and errors

5. **Evaluation Node**
   - Analyze command execution results
   - Update student's success rate
   - Identify struggling concepts

6. **Feedback Node**
   - Generate contextual, personalized response
   - Use retrieved documentation
   - Apply chosen tutoring strategy
   - Encourage learning

### 4. Graph Workflow (`graph.py`)

Defines the LangGraph state machine:
- Entry point: Understanding
- Conditional routing based on intent
- Multiple paths through the graph
- Exit: Feedback → END

### 5. Tutor Interface (`tutor.py`)

Main API for interacting with the tutoring agent:
```python
tutor = NetworkingLabTutor()
tutor.start_lab("01-basic-routing", mastery_level="novice")
response = tutor.ask("How do I configure an IP address?")
print(response["response"])
```

## Usage

### 1. Build RAG Index

First, index your lab documentation:

```bash
./scripts/build-rag-index.sh
```

This will:
- Load all `.md` files from `data/labs/`
- Chunk and embed documents
- Build FAISS index at `data/faiss_index/`

### 2. Test RAG Retrieval

Verify the retrieval system works:

```bash
./scripts/test-rag-retrieval.sh
```

### 3. Run the Tutor

Test the complete tutoring agent:

```bash
./scripts/test-tutor.sh
```

Or use programmatically:

```python
from orchestrator.tutor import NetworkingLabTutor

# Create tutor instance
tutor = NetworkingLabTutor()

# Start a lab
welcome = tutor.start_lab("01-basic-routing", mastery_level="novice")
print(welcome["response"])

# Ask questions
response = tutor.ask("How do I configure an IP address?")
print(response["response"])

# Check progress
progress = tutor.get_progress()
print(f"Progress: {progress['objectives_completed']}/{progress['total_objectives']}")
```

## Tutoring Strategies

### Socratic Method (Default for Novices)
- Ask guiding questions
- Help students discover answers
- Encourage critical thinking

### Direct Explanation
- Clear, step-by-step instructions
- Used when max hints reached
- Comprehensive coverage of topic

### Hints
- Partial information
- Points in right direction
- Incremental guidance

### Challenge (Advanced Students)
- Thought-provoking questions
- Extend concepts beyond basics
- Encourage experimentation

## Adding New Labs

1. Create lab document in `data/labs/XX-lab-name.md`
2. Follow the markdown structure of existing labs
3. Include:
   - Lab objectives
   - Step-by-step instructions with commands
   - Expected output
   - Explanations
   - Troubleshooting tips
4. Rebuild the RAG index: `./scripts/build-rag-index.sh`

## Configuration

The system uses dual-mode NIM configuration (see `config/README.md`):
- **Hosted mode**: Free NVIDIA API for development
- **Self-hosted mode**: Your own EKS deployment for production

Set `NIM_MODE=hosted` or `NIM_MODE=self-hosted` in `.env`.

## Dependencies

Install required packages:
```bash
pip install langchain langchain-text-splitters langchain-core \
    langgraph faiss-cpu tiktoken openai python-dotenv
```

## TODO

### High Priority
- [ ] Integrate NetGSim simulator API
- [ ] Implement command parsing and execution
- [ ] Add evaluation logic for command results
- [ ] Load lab objectives from documentation metadata

### Medium Priority
- [ ] Context window expansion (adjacent chunks)
- [ ] Lab progress persistence (save/load sessions)
- [ ] Multi-turn conversation improvements
- [ ] Better intent classification

### Low Priority
- [ ] Voice interface support
- [ ] Lab performance analytics
- [ ] Customizable tutoring strategies
- [ ] Multi-language support

## Testing

Run the complete test suite:
```bash
# Build index
./scripts/build-rag-index.sh

# Test retrieval
./scripts/test-rag-retrieval.sh

# Test tutor
./scripts/test-tutor.sh
```

## Files

```
orchestrator/
├── README.md              # This file
├── architecture.md        # Detailed architecture document
├── __init__.py           # Package initialization
├── state.py              # State definitions
├── nodes.py              # LangGraph node functions
├── graph.py              # LangGraph workflow definition
├── tutor.py              # Main tutor interface
├── rag_indexer.py        # RAG indexing pipeline
└── rag_retriever.py      # RAG retrieval system

data/
├── labs/                 # Lab documentation (markdown)
│   ├── 01-basic-routing.md
│   └── 02-static-routing.md
└── faiss_index/          # FAISS vector store
    ├── labs_index.faiss
    └── labs_index_metadata.pkl

scripts/
├── build-rag-index.sh    # Build FAISS index
├── test-rag-retrieval.sh # Test retrieval
└── test-tutor.sh         # Test complete system
```

## Performance

- RAG retrieval: ~200-500ms per query
- LLM generation: ~1-3s per response (depends on NIM mode)
- Total response time: ~2-4s per student interaction

With self-hosted NIMs on EKS:
- Embedding NIM: ~50ms per batch (32 texts)
- LLM NIM: ~1-2s for 200 tokens

## License

This project is part of the Agentic AI Unleashed hackathon.
