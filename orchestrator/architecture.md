# AI Networking Lab Tutor - Architecture

## Overview

An intelligent tutoring system that guides students through networking lab exercises using:
- **LangGraph**: Multi-agent orchestration with state machine
- **RAG**: Retrieval-augmented generation for lab documentation
- **NVIDIA NIMs**: LLM inference and embeddings
- **NetGSim**: Proprietary network simulator for hands-on command execution and verification

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Student Interface                        │
│              (Chat / Web UI / Terminal)                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Tutoring State Machine                    │   │
│  │                                                       │   │
│  │  1. Understand → 2. Retrieve → 3. Guide             │   │
│  │       ↓              ↓             ↓                 │   │
│  │  4. Execute → 5. Evaluate → 6. Feedback             │   │
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

## LangGraph State Machine

### State Definition

```python
class TutoringState(TypedDict):
    # Student interaction
    student_question: str
    conversation_history: List[Dict[str, str]]

    # Lab context
    current_lab: str
    lab_step: int
    lab_objectives: List[str]

    # Retrieved context
    retrieved_docs: List[str]
    relevant_concepts: List[str]

    # Command execution
    command_to_execute: Optional[str]
    execution_result: Optional[Dict]

    # Tutoring logic
    next_action: str  # "explain", "guide", "execute", "evaluate"
    feedback: str
    hints_given: int
    mastery_level: str  # "novice", "intermediate", "advanced"
```

### Agent Nodes

1. **Understanding Node**
   - Parse student input
   - Identify intent (question, command request, help)
   - Determine current knowledge level

2. **Retrieval Node**
   - Query FAISS index with embedding
   - Retrieve relevant lab documentation
   - Fetch related networking concepts

3. **Planning Node**
   - Decide tutoring strategy
   - Choose between: explain concept, provide hint, execute command
   - Adapt to student's mastery level

4. **Execution Node**
   - Send commands to simulator
   - Capture output and status
   - Handle errors gracefully

5. **Evaluation Node**
   - Analyze execution results
   - Check against expected outcomes
   - Update mastery level

6. **Feedback Node**
   - Generate personalized feedback
   - Provide next steps
   - Celebrate progress or guide correction

### Edges (Transitions)

```python
# Conditional routing based on state
def route_next_action(state: TutoringState) -> str:
    if state["next_action"] == "explain":
        return "retrieval"
    elif state["next_action"] == "execute":
        return "execution"
    elif state["next_action"] == "evaluate":
        return "evaluation"
    else:
        return "feedback"
```

## RAG System Design

### Document Corpus
- Lab exercise guides (Markdown)
- Networking concept explanations
- Command reference documentation
- Common troubleshooting scenarios

### Indexing Pipeline
```python
1. Load documents from /data/labs/
2. Chunk documents (512 tokens with 50 token overlap)
3. Generate embeddings using Embed NIM
4. Store in FAISS index
5. Save metadata (source, lab_id, concept)
```

### Retrieval Strategy
- **Query Expansion**: Rephrase student question for better matches
- **Hybrid Search**: Semantic (embedding) + keyword (BM25)
- **Reranking**: Score by relevance to current lab step
- **Context Window**: Top 3-5 most relevant chunks

## Tutoring Strategies

### Socratic Method
- Ask guiding questions
- Don't give direct answers immediately
- Help student discover solutions

### Adaptive Difficulty
- **Novice**: More detailed explanations, step-by-step guidance
- **Intermediate**: Hints and pointers, less hand-holding
- **Advanced**: Conceptual questions, challenge extensions

### Progressive Hints
1. General concept reminder
2. Relevant command syntax
3. Partial solution
4. Complete solution (last resort)

## Integration Points

### 1. NetGSim Simulator Integration
```python
from simulator_client import NetGSimClient

client = NetGSimClient(base_url=os.getenv("SIMULATOR_BASE_URL"))

# Execute command
result = client.execute_command(
    device="R1",
    command="show ip interface brief"
)
```

### 2. NIM Integration
```python
from config.nim_config import get_llm_client, get_embedding_client

llm = get_llm_client()  # Uses hosted or self-hosted based on NIM_MODE
embeddings = get_embedding_client()

# LLM for tutoring
response = llm.chat.completions.create(...)

# Embeddings for RAG
query_embedding = embeddings.embeddings.create(...)
```

### 3. FAISS Integration
```python
import faiss
import numpy as np

# Load index
index = faiss.read_index("data/faiss_index.bin")

# Search
query_vector = get_embedding(query)
distances, indices = index.search(query_vector, k=5)
```

## Deployment Architecture

### Development Mode (Hosted NIMs)
```
┌──────────────┐
│  Developer   │
│   Laptop     │
│              │
│ - LangGraph  │
│ - FAISS      │
│ - Hosted NIMs│ ← FREE!
└──────────────┘
```

### Production Mode (Self-Hosted)
```
┌─────────────────────────────────────┐
│         EKS Cluster                 │
│  ┌────────────┐  ┌────────────┐   │
│  │ LangGraph  │  │   Embed    │   │
│  │ Orchestr.  │←→│    NIM     │   │
│  │   Pod      │  │ (g6.xlarge)│   │
│  └────────────┘  └────────────┘   │
│        ↕                            │
│  ┌────────────┐  ┌────────────┐   │
│  │  NetGSim   │  │    LLM     │   │
│  │ Simulator  │  │    NIM     │   │
│  │            │  │(g6.4xlarge)│   │
│  └────────────┘  └────────────┘   │
└─────────────────────────────────────┘
```

## Data Flow Example

**Student:** "How do I configure an IP address on a router interface?"

1. **Understanding**: Parse question → Intent: "configure_interface"
2. **Retrieval**: Query FAISS → Retrieve IP configuration docs
3. **Planning**: Student is novice → Use Socratic method
4. **Feedback**:
   ```
   "Great question! Before we configure an IP address,
   what command would you use to enter interface configuration mode?

   Hint: Think about the structure of Cisco IOS commands:
   - Global config mode
   - Interface config mode
   - Apply settings"
   ```

5. **Student Response**: "configure terminal?"
6. **Evaluation**: Partially correct → Encourage and guide
7. **Feedback**:
   ```
   "Good start! 'configure terminal' enters global configuration mode.
   Now, which command enters interface configuration mode?

   Example: interface <type> <number>"
   ```

## Success Metrics

- **Learning Effectiveness**: Student progress through lab objectives
- **Engagement**: Questions asked, hints used
- **Mastery**: Command success rate, concept comprehension
- **Efficiency**: Time to complete labs, help requests

## Technology Stack

- **LangGraph**: State machine orchestration
- **LangChain**: Document processing, RAG utilities
- **FAISS**: Vector search
- **NVIDIA NIMs**: LLM and embeddings
- **Pydantic**: Data validation
- **FastAPI**: API server (optional)
