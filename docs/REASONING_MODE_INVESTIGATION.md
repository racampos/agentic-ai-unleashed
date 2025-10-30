# NVIDIA Nemotron Reasoning Mode Investigation

## Summary

We investigated enabling NVIDIA Nemotron's reasoning mode (which produces `<think></think>` tags containing the model's chain-of-thought) in the AI networking tutor.

## Key Finding

**Reasoning mode appears to improve response quality, but `<think>` tags are not visible in production responses.**

## What We Tested

### Working Standalone Test
Created `test_reasoning_mode.py` which successfully produces `<think>` tags:
- System message: `"detailed thinking on"`
- Streaming mode enabled: `stream=True`
- Result: ✅ Produced ~4774 characters of visible reasoning in `<think></think>` tags

### Production Environment Tests

Tested multiple configurations in `orchestrator/nodes.py`:

1. **Initial attempt**: Prepended "detailed thinking on" to system prompt
   - Result: ❌ No tags, but responses "felt more intelligent"

2. **Tried "reasoning on" instead of "detailed thinking on"**
   - Result: ❌ No visible difference

3. **Disabled tool calling** (hypothesis: tools interfere with reasoning mode)
   - Result: ❌ Still no tags, even with tools disabled

4. **Enabled streaming mode** (matching working test)
   - Result: ❌ Still no tags

5. **Minimal system prompt** (only "detailed thinking on", no other instructions)
   - Result: ❌ Still no tags, even with exact same config as working test

## Configuration Comparison

| Feature | Working Test | Production (All Attempts) |
|---------|--------------|---------------------------|
| System prompt | `"detailed thinking on"` | Tried both minimal and full prompts |
| Streaming | `stream=True` | Tried both True and False |
| Tool calling | None | Tried with and without tools |
| Conversation history | None | Tried with and without history |
| Client | `OpenAI()` | `OpenAI()` (identical) |
| API endpoint | NVIDIA hosted API | NVIDIA hosted API (identical) |
| Model | `llama-3.1-nemotron-nano-8b-v1` | Same model |
| `<think>` tags visible | ✅ Yes | ❌ No |

## Conclusion

Despite using identical configuration to the working test, production code does not show `<think>` tags. Possible explanations:

1. **Async context**: Production runs inside async LangGraph nodes while test is synchronous
2. **Unknown API behavior**: NVIDIA API may handle requests differently in certain contexts
3. **Internal filtering**: Tags may be generated but filtered out before reaching our code

However, user feedback indicated that **responses "feel more intelligent"** with reasoning mode enabled, suggesting the reasoning is happening internally even if tags aren't visible.

## Final Configuration

We've enabled reasoning mode in production with the following setup:

```python
# System prompt includes "detailed thinking on" prefix
system_prompt_with_reasoning = f"detailed thinking on\n\n{system_prompt}"

# LLM call includes recommended parameters
response = llm_client.chat.completions.create(
    model=llm_config["model"],
    messages=messages,
    tools=tools.TOOL_DEFINITIONS,
    tool_choice="auto",
    max_tokens=2048,  # Increased for reasoning
    temperature=0.6,   # Recommended for reasoning mode
    top_p=0.95,        # Recommended for reasoning mode
)
```

**Benefits:**
- Improved response quality (subjectively observed)
- Full tool calling functionality maintained
- Conversation history preserved
- No visible downsides

**Tradeoffs:**
- `<think>` tags not visible (cannot see reasoning process)
- Slightly higher token usage (max_tokens increased from 300 to 2048)

## Test Files Created

- `test_reasoning_mode.py`: Tests reasoning mode with/without "detailed thinking on"
- `test_reasoning_with_tools.py`: Tests reasoning mode with function calling enabled

## Recommendation

**Keep reasoning mode enabled.** Even though we can't see the `<think>` tags, the quality improvement is valuable and there are no significant downsides. The model appears to be reasoning internally even if we can't observe it directly.
