# LangGraph Architecture Quick Reference

## File Structure

```
orchestrator/
├── graph.py                    # Main LangGraph definition
├── nodes.py                    # Node implementations (13+ nodes)
├── state.py                    # TutoringState TypedDict (40+ fields)
├── tutor.py                    # NetworkingLabTutor (user-facing API)
├── tools.py                    # Tool definitions (get_device_running_config)
├── rag_retriever.py           # FAISS retrieval client
├── rag_indexer.py             # RAG indexing pipeline
└── error_detection/           # Error detection framework
    ├── detector.py            # Main ErrorDetector orchestrator
    ├── base.py                # BaseErrorPattern, FuzzyErrorPattern
    ├── registry.py            # PatternRegistry, JSON loader
    └── patterns/
        ├── hardcoded.json     # Manually-defined error patterns
        └── generated/         # Auto-generated patterns (if any)
```

## The 6 Key Nodes (After Phase 2.1)

### 1. intent_router_node
- **Role:** Route between teaching and troubleshooting
- **Input:** student_question, cli_history
- **Output:** intent (teaching|troubleshooting|ambiguous)
- **Logic:** Keyword matching + CLI error detection
- **Time:** <100ms

### 2. teaching_retrieval_node (Teaching Path)
- **Role:** Retrieve conceptual documentation
- **Input:** student_question, current_lab
- **Output:** retrieved_docs (k=3, concept-focused)
- **Logic:** Query expansion "Explain the concept: ..."
- **Time:** 200-500ms

### 3. teaching_feedback_node (Teaching Path) 🔄
- **Role:** Generate conceptual explanation
- **Input:** student_question, retrieved_docs, mastery_level
- **Output:** feedback_message
- **Logic:** LLM call focused on understanding, not procedures
- **Time:** 2-5s

### 4. retrieval_node (Troubleshooting Path)
- **Role:** Smart error-focused retrieval
- **Input:** student_question, cli_history, current_lab
- **Output:** retrieved_docs (k=12, error-prioritized)
- **Logic:** Error detection → query enhancement → prioritization
- **Time:** 300-700ms

### 5. feedback_node (Troubleshooting Path) 🔄
- **Role:** Complex error diagnosis + tool support
- **Input:** 10+ state fields (docs, cli_history, etc.)
- **Output:** feedback_message, updated conversation_history
- **Logic:** Inline error detection, tool calling (max 3 iterations), reasoning mode
- **Time:** 5-15s
- **Critical:** Only calls tools if NO CLI errors present

### 6. paraphrasing_node (Troubleshooting Path) 🔄
- **Role:** Clean up response
- **Input:** feedback_message
- **Output:** cleaned feedback_message
- **Logic:** Remove preambles, internal codes, tool references
- **Time:** 1-3s

## State Schema (Key Fields)

**Routing Fields:**
- `intent: Literal["teaching", "troubleshooting", "ambiguous"]`
- `tutoring_strategy: Literal["socratic", "direct", "hint", "challenge"]`

**Critical Context:**
- `cli_history: List[Dict]` - Last 5 commands with outputs (CRUCIAL)
- `student_question: str` - Current user input
- `retrieved_docs: List[str]` - RAG results (4-5 documents)
- `lab_instructions: str` - Full lab description (5000 chars)

**Output:**
- `feedback_message: str` - Response to user

**Error Detection (POC):**
- `cli_diagnoses: List[Dict]` - Cached error diagnoses (preprocessed)

## Graph Flow Diagram

```
intent_router_node
    ↓
    intent="teaching" → teaching_retrieval → teaching_feedback → END
    intent="troubleshooting" → retrieval → feedback → paraphrasing → END
    intent="ambiguous" → teaching_retrieval → teaching_feedback → END
```

## Integration Points

### Error Detection
- **Where:** In feedback_node during CLI context building
- **Implementation:** `error_detector.detect(command, output)` returns:
  - `error_type` (TYPO_IN_COMMAND, WRONG_MODE, CIDR_NOT_SUPPORTED)
  - `diagnosis` (templated explanation)
  - `fix` (templated solution with examples)
  - `metadata` (pattern_id, fuzzy_match_info)
- **Usage:** Injected into system prompt with ⚠️, 📋, ✅ icons

### RAG Retrieval
- **Teaching:** k=3, simple query "Explain the concept: X"
- **Troubleshooting:** k=12, enhanced query based on error detection
- **Prioritization:**
  - If errors: error_patterns (2) + command_ref (2) + lab_specific (1)
  - Else: command_ref (3) + lab_specific (2)

### Tool Calling
- **Tool:** `get_device_running_config(device_name: str)`
- **When:** Enabled ONLY if NO CLI errors visible
- **Iteration:** Max 3 LLM calls (check → execute → result → response)

### Reasoning Mode
- **Activation:** Prepend "detailed thinking on\n\n" to system prompt
- **Benefit:** Enhanced reasoning for complex error diagnosis

## Performance Profile

| Node | Time | Complexity |
|------|------|-----------|
| intent_router | <100ms | Very Low |
| teaching_retrieval | 200-500ms | Low |
| teaching_feedback | 2-5s | Low |
| retrieval | 300-700ms | Medium |
| feedback | 5-15s | Very High |
| paraphrasing | 1-3s | Low |

**Teaching Path Total:** ~2.5-5.5s
**Troubleshooting Path Total:** ~6-20s (longer due to complexity + tools)

## Implementation History

- Proactive CLI error detection (streaming, preprocessed diagnoses)
- Teaching path with conditional routing integration
- Added teaching_retrieval_node and teaching_feedback_node
- Added intent_router_node with heuristic classification
- Simplified troubleshooting from 8 to 3 nodes

## Async/Streaming

**Async Nodes** (🔄 symbol):
- teaching_feedback_node
- feedback_node
- paraphrasing_node

**Streaming Support:**
- `tutor.ask_stream()` → yields chunks as they arrive
- Calls `feedback_node_stream()` directly (not through graph)
- Phases: prepare → tool-check → execute-tools → stream-response

## Usage Examples

```python
# Visualize graph
from orchestrator.graph import create_tutoring_graph
graph = create_tutoring_graph().compile()
print(graph.get_graph().draw_mermaid())

# Test error detection
from orchestrator.error_detection import get_default_detector
detector = get_default_detector()
result = detector.detect("hostnane Router1", output)
print(result.error_type, result.diagnosis, result.fix)

# Run demo
from orchestrator.tutor import NetworkingLabTutor
tutor = NetworkingLabTutor()
tutor.start_lab("01-basic-routing")
response = await tutor.ask("How do I configure IP?")
print(response["response"])
```

## Key Design Decisions

1. **Dual-Path Architecture:** Teaching ≠ Troubleshooting
   - Teaching: Lightweight, educational, conceptual
   - Troubleshooting: Heavy, grounded, error-focused

2. **Heuristic Intent Routing:** Fast keyword-based (not LLM)
   - Runs in <100ms
   - Considers CLI error history as strong signal
   - Can be upgraded to LLM-based later

3. **Error Detection First:** Patterns before LLM reasoning
   - Specific diagnosis (typo, mode, syntax)
   - Saves time vs having LLM re-analyze
   - Fuzzy matching for typos (hostnane → hostname)

4. **Smart Tool Disabling:** Avoid tools when CLI errors visible
   - Reduces latency
   - Prevents hallucination
   - Error diagnosis sufficient from docs + context

5. **RAG Prioritization:** Error patterns first
   - When errors detected, show relevant error documentation
   - Students get targeted help, not generic docs

6. **Reasoning Mode:** Enhanced LLM thinking
   - Prepend "detailed thinking on" to system prompt
   - Better error diagnosis via extended reasoning
   - Visible in token budget (~2-4K additional tokens)

## Common Patterns

**Query Enhancement in retrieval_node:**
```python
if error_marker_detected:
    query = "Invalid input detected [cmd_keywords] error pattern"
elif error_keywords:
    query = "[error_type] [cmd_keywords] Cisco IOS"
else:
    query = "Cisco IOS [cmd_keywords] command syntax"
```

**Error Context Injection in feedback_node:**
```python
if error_detected:
    cli_context += f"⚠️ ERROR TYPE: {result.error_type}\n"
    cli_context += f"📋 DIAGNOSIS: {result.diagnosis}\n"
    cli_context += f"✅ FIX: {result.fix}\n"
```

**Tool Iteration in feedback_node:**
```python
for iteration in range(3):
    response = llm_client.create(messages=messages, tools=tools_list)
    if not response.tool_calls:
        break
    # Execute tools and add to messages
    # Loop continues with tool results
```

## Potential Enhancements

1. Upgrade intent classification to LLM-based
2. Auto-generate error patterns from student examples
3. Add quiz/comprehension checks in teaching path
4. Implement multi-turn error pattern learning
5. Expand tools (execute_command, create_interface)
6. Better mastery_level tracking and response complexity adjustment

