# LangGraph Multi-Agent Architecture

## Overview

This document describes a sophisticated **dual-path LangGraph workflow** for an AI-powered networking lab tutoring system. The architecture distinguishes between two pedagogical paths:

1. **Teaching Path** - For conceptual/educational questions
2. **Troubleshooting Path** - For error diagnosis and debugging

The system integrates advanced error detection, RAG-based retrieval, tool-based device configuration queries, and streaming responses.

---

## Overall Architecture

### High-Level Design Pattern

```
Student Input
    ↓
Intent Router (Keyword & CLI History Detection)
    ↓
Conditional Routing (Based on Classified Intent)
    ├─→ Teaching Path
    │     ├─→ Teaching Retrieval (Query Expansion for Concepts)
    │     └─→ Teaching Feedback (Conceptual Explanation)
    │           └─→ END
    │
    └─→ Troubleshooting Path
          ├─→ Retrieval (RAG with Error-Focused Query Enhancement)
          ├─→ Feedback (Error Diagnosis + Tool Support + LLM with Reasoning)
          ├─→ Paraphrasing (Response Cleanup)
          └─→ END
```

### Key Architecture Components

1. **LangGraph State Machine** (`orchestrator/graph.py`)
   - Entry point: `intent_router_node`
   - Two branching paths with conditional edges
   - Fully async/streaming-capable

2. **State Management** (`orchestrator/state.py`)
   - Single `TutoringState` TypedDict flows through entire pipeline
   - Comprehensive 150+ field state covering interaction, lab context, CLI history, RAG results, tutoring logic

3. **Node Implementation** (`orchestrator/nodes.py`)
   - 13+ nodes implementing various tutoring stages
   - Async nodes for LLM interaction
   - Tool-calling support with iteration logic

4. **Error Detection Framework** (`orchestrator/error_detection/`)
   - Pattern-based error matching (regex + signatures)
   - Fuzzy matching for typo detection
   - Priority-ordered pattern registry
   - Support for both hardcoded and generated patterns

5. **RAG System** (`orchestrator/rag_retriever.py`, `rag_indexer.py`)
   - FAISS vector index for semantic search
   - Smart document prioritization (error patterns > command reference > lab-specific)
   - Query enhancement based on detected errors

6. **Tool Support** (`orchestrator/tools.py`)
   - `get_device_running_config()` - Retrieve live device configurations
   - Tool calling integrated into feedback node with iteration support
   - Disabled when CLI errors are present (to prevent hallucination)

---

## Node Reference

### Entry Point & Routing

#### 1. **intent_router_node** ⭐ (Critical - Routes Everything)
**Purpose:** Classify user intent to determine which path to follow

**Input State Fields:**
- `student_question` - The user's input
- `cli_history` - Recent CLI commands/outputs

**Classification Logic:**
```python
Teaching Keywords:
  "why do we need", "why do i need", "what is", "what does",
  "explain", "how does", "tell me about", "describe",
  "when should", "difference between"

Troubleshooting Keywords:
  "wrong", "error", "fix", "not working", "failed", "stuck",
  "what am i doing", "why won't", "doesn't work"

Strong Signal: Recent CLI Errors → troubleshooting (unless asking conceptual question)
```

**Output State Updates:**
- `intent: Literal["teaching", "troubleshooting", "ambiguous"]`

**Conditional Routing:**
```
intent="teaching" → teaching_retrieval
intent="troubleshooting" → retrieval  
intent="ambiguous" → teaching_retrieval (default)
```

**Key Features:**
- Heuristic-based (keyword matching + CLI error detection)
- Recent CLI errors override keyword signals
- Conceptual questions can bypass errors

---

### Teaching Path (For Conceptual Questions)

#### 2. **teaching_retrieval_node**
**Purpose:** Retrieve conceptual documentation for learning questions

**Input State Fields:**
- `student_question`
- `current_lab`

**Processing:**
1. Query expansion: `f"Explain the concept: {student_question}"`
2. FAISS retrieval with k=3 (fewer docs than troubleshooting)
3. No CLI context needed - pure documentation retrieval

**Output State Updates:**
- `retrieved_docs: List[str]` - Raw document content
- `retrieval_query: str` - Query used for retrieval

**Optimization:** Smaller k value and simpler query for focused conceptual answers

---

#### 3. **teaching_feedback_node** 🔄 (Async)
**Purpose:** Generate clear conceptual explanations without CLI noise

**Input State Fields:**
- `student_question`
- `retrieved_docs`
- `mastery_level`

**Processing:**
1. Build context from retrieved docs
2. System prompt emphasizes:
   - Conceptual clarity over procedures
   - "Why" and "when" over "how"
   - No CLI instructions unless specifically asked
   - Clear but concise responses (2-4 sentences for simple, 1-2 paragraphs for complex)
3. LLM call with temperature=0.7, max_tokens=400

**Output State Updates:**
- `feedback_message: str` - The educational response

**Key Feature:** Tone is friendly, encouraging, focused on understanding - NOT CLI procedures

---

### Troubleshooting Path (For Error Diagnosis)

#### 4. **retrieval_node**
**Purpose:** Smart retrieval focused on error diagnosis and command syntax

**Input State Fields:**
- `student_question`
- `current_lab`
- `cli_history` - Last 5 commands with outputs

**Query Enhancement Logic:**
```
if error_marker_detected (^) in recent commands:
  → Priority: Error patterns + Command syntax
  → Query: "Invalid input detected [command_keywords] error pattern"

elif other_error_keywords:
  → Query: "[error_type] [command_keywords] Cisco IOS"

elif command_keywords_only:
  → Query: "Cisco IOS [command_keywords] command syntax"

else:
  → Query: "Cisco IOS {original_question}"
```

**Three-Stage Document Prioritization:**
1. **Error Pattern Chunks** (cisco-ios-error-patterns.md) - Top priority if errors detected
2. **Command Reference** (cisco-ios-command-reference.md) - Always included
3. **Lab-Specific** (current lab docs) - Situational context

**RAG Search:** k=12 to get diverse results, then selectively takes top 4-5

**Output State Updates:**
- `retrieved_docs: List[Dict]` - Documents with metadata and scores
- `retrieval_query: str` - Enhanced query used

**Key Feature:** Detects error patterns and prioritizes relevant documentation

---

#### 5. **feedback_node** 🔄 (Async - Complex, Multi-Stage)
**Purpose:** Generate personalized feedback using retrieved docs, CLI history, error detection, and tools

**Input State Fields:**
- `student_question`
- `retrieved_docs`
- `cli_history` - Last 5 commands analyzed
- `conversation_history`
- `mastery_level`
- `tutoring_strategy` - "socratic", "direct", "hint", "challenge"
- `lab_*` fields - Lab context (title, description, topology, objectives, instructions)

**Processing Pipeline:**

1. **CLI Context Building** (with inline error detection):
   ```
   For each recent CLI command:
     - Display command and output
     - If error detected:
       * Run error_detector.detect(cmd, output)
       * Inject error_type, diagnosis, fix inline
       * Mark with ⚠️ and ✅ icons
   ```

2. **Preprocessed Diagnosis Context**:
   ```
   if cli_diagnoses cached in state:
     - Build "PREPROCESSED ERROR DIAGNOSES" section
     - Direct LLM to paraphrase these, not re-analyze
     - Critical for "What am I doing wrong?" questions
   ```

3. **RAG Documentation Context**:
   ```
   Build labeled sections for:
     [ERROR PATTERN GUIDE] - Doc i
     [CISCO IOS COMMAND REFERENCE] - Doc i
     [LAB CONTEXT] - Doc i
   ```

4. **System Prompt with Multiple Strategies**:
   ```
   Reasoning activation: "detailed thinking on\n\n{system_prompt}"
   
   Communication style: Authority + Confidence (not hedging)
   
   Critical instructions:
     - Read terminal activity as source of truth
     - Use ^ marker to identify exact error location
     - If error pattern was detected, paraphrase diagnosis/fix
     - Compare CLI context with documentation
     - Use get_device_running_config tool ONLY when needed
     - Strict CIDR notation rule (use dotted decimal, not /24)
     - Keep responses concise (1-2 sentences for simple, 3-5 for complex)
   ```

5. **Tool Calling with Iteration**:
   ```
   CRITICAL: Only call tools if NO CLI ERRORS are present
   
   Max iterations: 3
   
   Iteration loop:
     - Call LLM with tools enabled (if allowed)
     - If LLM requests tool calls:
       * Execute each tool
       * Add results to message stream
       * Re-invoke LLM with tool results
     - If no tool calls: Return response
   ```

6. **Conversation History Integration**:
   - Last 4 messages (2 turns) added for context
   - Response added to history for continuity

**Output State Updates:**
- `feedback_message: str` - Main response (may contain reasoning markers)
- `conversation_history: List[Dict]` - Updated with new exchange
- `total_interactions: int` - Incremented

**Key Features:**
- **Error detection integration**: Automatically diagnoses CLI errors inline
- **Tool support**: Can query device configs when needed
- **Reasoning mode**: Prepends "detailed thinking on" for enhanced reasoning
- **Smart tool disabling**: Prevents tool calls when errors are visible (avoids hallucination)
- **Context prioritization**: CLI history > Documentation > Tool calls

---

#### 6. **paraphrasing_node** 🔄 (Async)
**Purpose:** Clean up feedback by removing verbose preambles and internal references

**Input State Fields:**
- `feedback_message` - Raw feedback from feedback_node

**Processing:**
1. LLM-based cleanup prompt removes:
   - Verbose preambles ("Based on...", "Looking at...")
   - Internal error codes (TYPO_IN_COMMAND, WRONG_MODE, etc.)
   - Tool references (get_device_running_config mentions)
   - Quotes wrapping responses

2. Maintains actionable content (commands, examples, explanations)

3. Temperature=0.1 for consistent, deterministic cleaning

4. Max_tokens=500 for typical responses

**Output State Updates:**
- `feedback_message: str` - Cleaned version

**Fallback:** Returns original if cleaning fails

**Key Feature:** Ensures user sees clean, professional responses without internal implementation details

---

## State Schema (TutoringState)

### State Structure Overview
The `TutoringState` TypedDict defines 40+ fields organized in logical sections:

```
TutoringState = {
    # ========== STUDENT INTERACTION ==========
    student_question: str              # Current user input
    conversation_history: List[Dict]   # Full chat history {role, content}

    # ========== LAB CONTEXT ==========
    current_lab: str                   # Lab ID
    lab_title: str                     # Human-readable title
    lab_description: str               # Brief description
    lab_instructions: str              # Full markdown instructions
    lab_step: int                      # Current step
    lab_objectives: List[str]          # Learning objectives
    completed_objectives: List[str]    # Completed so far
    lab_topology_info: Optional[Dict]  # {device_count, connection_count, devices: []}

    # ========== RAG CONTEXT ==========
    retrieved_docs: List[str]          # Document chunks from FAISS
    relevant_concepts: List[str]       # Extracted concepts
    retrieval_query: str               # Query used for RAG

    # ========== COMMAND EXECUTION ==========
    command_to_execute: Optional[str]
    execution_result: Optional[Dict]
    expected_output: Optional[str]

    # ========== CLI CONTEXT (CRITICAL) ==========
    cli_history: List[Dict]            # [{command, output, timestamp, device_id}]
    current_device_id: Optional[str]   # Active device
    simulator_devices: Dict            # Device registry
    ai_suggested_command: Optional[str]
    ai_intervention_needed: bool
    cli_diagnoses: List[Dict]          # POC: Preprocessed error diagnoses

    # ========== ROUTING & STRATEGY ==========
    intent: Literal["teaching", "troubleshooting", "ambiguous"]  # From intent_router
    student_intent: Literal["question", "command", "help", "next_step"]
    next_action: Literal["explain", "guide", "execute", "evaluate", "feedback"]
    tutoring_strategy: Literal["socratic", "direct", "hint", "challenge"]
    feedback_message: str              # Response to student

    # ========== TEACHING LOGIC ==========
    hints_given: int
    max_hints: int
    
    # ========== PROGRESS TRACKING ==========
    mastery_level: Literal["novice", "intermediate", "advanced"]
    success_rate: float
    concepts_understood: List[str]
    struggling_with: List[str]
    
    # ========== SESSION METADATA ==========
    session_id: str
    start_time: str
    total_interactions: int
}
```

### Critical State Flows

**Teaching Path Flow:**
```
intent_router → intent="teaching"
  → teaching_retrieval: updates retrieved_docs
  → teaching_feedback: consumes retrieved_docs, produces feedback_message
  → END
```

**Troubleshooting Path Flow:**
```
intent_router → intent="troubleshooting"
  → retrieval: analyzes cli_history, enhances query, gets retrieved_docs
  → feedback: uses cli_history+retrieved_docs+tools, produces feedback_message
  → paraphrasing: cleans feedback_message
  → END
```

---

## Integration Points

### 1. Error Detection Integration ⭐

**Implementation:**
```python
# In feedback_node (line 414-425)
if "Invalid input" in output or "Incomplete command" in output or "%" in output:
    detection_result = error_detector.detect(cmd, output)
    if detection_result:
        cli_context += f"⚠️ ERROR TYPE: {detection_result.error_type}\n"
        cli_context += f"📋 DIAGNOSIS: {detection_result.diagnosis}\n"
        cli_context += f"✅ FIX: {detection_result.fix}\n"
```

**Detection Result Fields:**
- `error_type: str` - TYPO_IN_COMMAND, WRONG_MODE, CIDR_NOT_SUPPORTED, etc.
- `diagnosis: str` - Why the error occurred (templated)
- `fix: str` - How to correct it (templated with examples)
- `metadata: Dict` - pattern_id, variables extracted from regex, fuzzy match info

**Pattern Matching Pipeline:**
1. Check all signatures present in output
2. Match command against regex pattern
3. Optional: validate ^ marker position
4. Extract variables from matches
5. Template diagnosis and fix messages
6. (Optional) Fuzzy match for typo identification

**Fuzzy Matching Feature:**
- Extracts word at ^ marker position
- Mode-aware command vocabulary lookup
- Returns similarity score
- Identifies specific typos like "hostnane" → "hostname"

### 2. RAG Integration ⭐

**Retrieval Flow (In retrieval_node and feedback_node_stream):**
```
1. Process cli_history for error patterns and command keywords
2. Build enhanced retrieval_query based on detected patterns
3. FAISS semantic search with k=12 (troubleshooting) or k=3 (teaching)
4. Categorize results: error_patterns, command_ref, lab_specific
5. Prioritize based on detected error type
6. Select final top 4 documents for LLM context
```

**Smart Prioritization Logic:**
```python
if has_error_marker or error_keywords:
    # ERROR PATH: Error patterns first
    retrieved_docs = error_pattern_chunks[:2]
    + command_ref_chunks[:2]
    + lab_specific_chunks[:1]
else:
    # STANDARD PATH: Command reference first
    retrieved_docs = command_ref_chunks[:3]
    + lab_specific_chunks[:2]
```

**Document Types:**
- **cisco-ios-error-patterns.md** - Error explanations with fixes
- **cisco-ios-command-reference.md** - Syntax and examples
- **Lab-specific docs** - Current lab context and requirements

### 3. Intent-Based Routing ⭐

**Teaching vs Troubleshooting Decision Tree:**

```
START: student_question

IF has_recent_cli_errors:
    IF teaching_keywords > 0 AND troubleshooting_keywords == 0:
        → TEACHING (asking conceptual question despite errors)
    ELSE:
        → TROUBLESHOOTING (focused on fixing)
        
ELIF troubleshooting_keywords > teaching_keywords:
    → TROUBLESHOOTING

ELIF teaching_keywords > troubleshooting_keywords:
    → TEACHING

ELIF teaching_keywords == troubleshooting_keywords AND keywords > 0:
    → AMBIGUOUS (equal signals)

ELSE:
    → TEACHING (default for general questions)
```

### 4. Tool Calling ⭐

**Tool Definition:**
```python
get_device_running_config(device_name: str) -> str
```

**When Tools Are Called:**
- Student asks about current device config (IP addresses, routes, VLANs)
- LLM decides it needs live state information

**When Tools Are DISABLED:**
- CLI errors are present (avoids tool-calling overhead when diagnosing errors)
- Prevents hallucination when student has visible failures

**Iteration Logic:**
```
1. Call LLM with messages + tools
2. If tool_calls in response:
     a. Execute each tool call
     b. Add results to messages as "role": "tool"
     c. Re-invoke LLM with augmented messages
     d. LLM should now have context for better response
3. If no tool_calls: Use response as-is
4. Max 3 iterations to prevent loops
```

### 5. Paraphrasing/Response Cleanup

**Removes:**
- "Based on the critical information provided..."
- "Based on the terminal activity..."
- Internal error codes (TYPO_IN_COMMAND, WRONG_MODE, CIDR_NOT_SUPPORTED)
- Tool references ("Use get_device_running_config")
- Surrounding quotes

**Keeps:**
- Commands and examples
- Explanations and advice
- Conversational tone

**Result:** User sees professional, clean responses without implementation details

---

## Implementation Details

### Teaching Path Integration

The system includes two primary paths:

**Teaching Path:**
- `teaching_retrieval_node` for conceptual docs
- `teaching_feedback_node` for educational responses
- Simplified prompts focused on concepts
- Flow: `teaching_retrieval` → `teaching_feedback` → END

**Troubleshooting Path:**
- `retrieval` → `feedback` → `paraphrasing` → END
- Enhanced error detection and tool support

**Routing:**
- `route_by_intent()` conditional edges function
- Ambiguous cases default to teaching_retrieval

### Proactive CLI Error Detection

**Features:**
1. **Preprocessed diagnosis context** - `cli_diagnoses` state field
   - Stores error diagnoses from previous commands
   - Injected into feedback_node system prompt
   - Allows paraphrasing rather than re-processing

2. **Error detection in nodes.py** - Inline diagnosis (lines 414-425)
   - Detects errors during CLI context building
   - Marks with ⚠️, 📋, ✅ icons
   - Provides detection result to LLM

3. **Streaming feedback_node** - `feedback_node_stream()` (lines 1020-1525)
   - Async generator that yields streaming chunks
   - Multi-stage retrieval with error-focused prioritization
   - Tool calling with 2-phase approach (check → execute → stream)
   - System prompt with reasoning mode enabled

### Streaming Architecture

**User Flows:**

**Sync Path (tutor.ask()):**
```
ask() → graph.ainvoke(state) → returns full result
```

**Streaming Path (tutor.ask_stream()):**
```
ask_stream():
  1. Call feedback_node_stream(state) - yields chunks
  2. For each chunk:
       - If type="content": yield text chunk
       - If type="info": yield metadata
       - If type="metadata": yield progress/suggestions
  3. Update state after completion
  4. Yield final metadata
```

**Streaming Details (feedback_node_stream):**
- Phase 1: Non-streaming LLM call to check for tool needs
- Phase 2: If tools needed, execute them and add to messages
- Phase 3: Stream final response back to client
- Filtering: Removes `<TOOLCALL>` and `<THINKING>` tags from output

---

## Key Implementation Details

### Error Detection Pattern System

**Pattern Types:**
1. **RegexErrorPattern** - Signature + regex matching
   - `signatures: List[str]` - Must all be present in output
   - `command_pattern: {regex, flags}` - Command must match
   - `diagnosis_template` - Variables interpolated from regex groups
   - `fix_template` - Same interpolation

2. **FuzzyErrorPattern** - Extends RegexErrorPattern
   - Adds typo detection via fuzzy matching
   - Extracts word at ^ marker
   - Finds similar valid Cisco IOS command
   - Returns similarity score

**Priority System:**
- Patterns checked in priority order (higher first)
- First match wins (short-circuit)
- Registry can filter by priority, type, or mode

**Metadata:**
```python
{
    "affected_modes": ["global_config", "interface_config"],
    "pattern_id": "TYPO_IN_COMMAND_v1",
    "variables": {"command": "...", "typo_word": "...", "suggested": "..."},
}
```

### Cisco Command Vocabulary

**File:** `orchestrator/error_detection/cisco_commands.json`

**Structure:**
```json
{
    "commands": {
        "common_keywords": [...],
        "global_config": [...],
        "interface_config": [...],
        "line_config": [...],
        "router_config": [...]
    }
}
```

**Used for:**
- Fuzzy matching in typo detection
- Mode-aware command validation

### Streaming Response Pipeline

**response_node_stream Processing:**
```
1. Build CLI context (with inline error detection)
2. Build diagnosis context (from preprocessed diagnoses)
3. Build RAG context (smart retrieval with error prioritization)
4. Create system prompt with reasoning mode
5. Determine if tools should be enabled
6. Phase 1: Non-streaming call → check for tool needs
7. If tools needed:
     a. Yield "info" type message
     b. Execute tools
     c. Add to message stream
8. Phase 2: Streaming call → stream response
9. Filter out internal markers
10. Yield content chunks
```

---

## Configuration & Dependencies

### LLM Configuration
**File:** `config/nim_config.py`

**Client Setup:**
- `get_llm_client()` - OpenAI-compatible NVIDIA NIM client
- `get_embedding_client()` - For vector embeddings
- Supports reasoning mode ("detailed thinking on" prepend)

**Models:**
- LLM: Claude or similar (reasoning-capable)
- Embeddings: `nv-embedqa-e5-v5` (1024-dimensional)

### FAISS Index Setup

**Files:**
- `data/faiss_index/labs_index.faiss` - Vector index
- `data/faiss_index/labs_index_metadata.pkl` - Metadata

**Chunking:**
- Size: 512 tokens
- Overlap: 50 tokens
- Splitters: Markdown headings, paragraphs, sentences

### Lab Data

**Directory:** `data/labs/`

**Content:**
- Each lab: YAML frontmatter + Markdown content
- Indexed during startup via `LabDocumentIndexer`
- Retrieved via semantic similarity

---

## Performance Characteristics

### Node Execution Time (Approximate)

1. **intent_router** - <100ms (keyword matching only)
2. **teaching_retrieval** - 200-500ms (RAG embedding + search)
3. **teaching_feedback** - 2-5s (LLM call with temperature=0.7)
4. **retrieval** - 300-700ms (RAG with query enhancement)
5. **feedback** - 5-15s (Complex LLM with tool support + iteration)
6. **paraphrasing** - 1-3s (LLM cleanup pass)
7. **feedback_node_stream** - Same as feedback but incremental

### Streaming Advantages

- User sees first token in ~2-3s (vs ~15s for full response)
- Progressive display improves perceived performance
- Suitable for long-form conceptual explanations

### Token Budget

**Per Request (typical):**
- System prompt: 2,000-3,000 tokens
- CLI history (5 commands): 1,000-2,000 tokens
- RAG docs (4 chunks): 1,000-1,500 tokens
- Conversation history (2 turns): 500-1,000 tokens
- Reasoning output: 2,000-4,000 tokens
- **Total: ~8,000-12,000 tokens/request**

---

## Testing & Debugging

### Graph Visualization

**File:** `orchestrator/graph.py`

```python
if __name__ == "__main__":
    graph = create_tutoring_graph()
    compiled = graph.compile()
    print(compiled.get_graph().draw_mermaid())
```

### Error Detection Tests

**File:** `orchestrator/error_detection/tests.py`

Includes:
- Pattern loading tests
- Detection accuracy tests
- Fuzzy matching validation
- Marker extraction tests

### Logging

**Component Logging:**
```python
# Error detection
[INTENT_ROUTER] Teaching (conceptual despite errors): ...
[TEACHING_RETRIEVAL] Retrieved 3 docs
[TEACHING_FEEDBACK] Generated 245 chars
[FEEDBACK_NODE] Detected error: TYPO_IN_COMMAND for command 'hostnane'
[Tool Calling] Iteration 1/3
[Paraphrasing] Original length: 1245, Cleaned length: 980
[FEEDBACK_NODE_STREAM] Starting new interaction
[FEEDBACK_NODE_STREAM] LLM requested 1 tool calls
```

---

## Key Features

1. **Dual-Path Design**
   - Teaching and troubleshooting handled separately
   - Teaching: lightweight, focused on concepts
   - Troubleshooting: heavy-weight, tool-enabled

2. **Error Handling**
   - Inline error detection during context building
   - Preprocessed diagnoses reduce re-processing
   - Fuzzy matching identifies specific typos
   - Priority-based pattern matching

3. **Flexible Routing**
   - Heuristic-based (fast) intent classification
   - Can be extended to LLM-based if needed
   - Handles ambiguous cases gracefully

4. **Tool Integration**
   - Iteration logic for tool calling
   - Disabled when not needed (CLI errors present)
   - 2-phase approach for streaming

5. **RAG Optimization**
   - Query enhancement based on detected patterns
   - Document prioritization (error patterns first)
   - Lab-specific filtering available
   - Semantic search with metadata

6. **Streaming Architecture**
   - Progressive response delivery
   - Filtering of internal implementation markers
   - Async throughout the pipeline

---

## Potential Enhancements

1. **Intent Classification Enhancement**
   - Upgrade to LLM-based classification (more nuanced)
   - Add student_intent field usage in feedback strategy

2. **Error Pattern Expansion**
   - Auto-generate from student error examples
   - Expand beyond hardcoded + JSON patterns

3. **Personalization**
   - Leverage mastery_level tracking more fully
   - Adjust response complexity dynamically

4. **Multi-Turn Error Context**
   - Learn from repeated error patterns
   - Expand beyond last 5 commands

5. **Teaching Path Enhancement**
   - Add quiz/comprehension checks after teaching
   - Track which concepts students struggle with

6. **Tool Calling Expansion**
   - Add execute_command, create_interface, etc.
   - Expand beyond get_device_running_config

---

## Summary

This architecture provides a **production-grade multi-agent system** with:
- Clear separation of concerns (teaching vs troubleshooting)
- Error detection with fuzzy matching
- RAG-powered documentation grounding
- Tool-calling support with iteration
- Streaming capabilities for better UX
- Comprehensive state management

The dual-path design addresses the fundamental difference between helping students learn concepts vs helping them debug configuration errors.
