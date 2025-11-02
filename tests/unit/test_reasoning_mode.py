"""
Test script to verify NVIDIA Nemotron reasoning mode works with their API.

This replicates the example from NVIDIA's playground to confirm that
"detailed thinking on" produces <think></think> tags in the response.
"""

import os
from openai import OpenAI

# Load API key from environment
api_key = os.getenv("NGC_API_KEY")
if not api_key:
    print("ERROR: NGC_API_KEY environment variable not set")
    exit(1)

print("Testing NVIDIA Nemotron reasoning mode...")
print("=" * 80)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

print("\nTest 1: WITH reasoning mode (detailed thinking on)")
print("-" * 80)

completion = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    messages=[
        {"role": "system", "content": "detailed thinking on"},
        {"role": "user", "content": "How can I calculate the integral of sin(x)?"}
    ],
    temperature=0.6,
    top_p=0.95,
    max_tokens=4096,
    stream=True
)

response_with_reasoning = ""
for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)
        response_with_reasoning += content

print("\n\n" + "=" * 80)
print("\nTest 2: WITHOUT reasoning mode (no system prompt)")
print("-" * 80)

completion = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    messages=[
        {"role": "user", "content": "How can I calculate the integral of sin(x)?"}
    ],
    temperature=0.6,
    top_p=0.95,
    max_tokens=4096,
    stream=True
)

response_without_reasoning = ""
for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)
        response_without_reasoning += content

print("\n\n" + "=" * 80)
print("\nAnalysis:")
print("-" * 80)

# Check for <think> tags
has_think_tags_with = "<think>" in response_with_reasoning
has_think_tags_without = "<think>" in response_without_reasoning

print(f"\nResponse WITH reasoning mode:")
print(f"  - Length: {len(response_with_reasoning)} characters")
print(f"  - Contains <think> tags: {has_think_tags_with}")

print(f"\nResponse WITHOUT reasoning mode:")
print(f"  - Length: {len(response_without_reasoning)} characters")
print(f"  - Contains <think> tags: {has_think_tags_without}")

if has_think_tags_with:
    # Extract thinking content
    import re
    think_match = re.search(r'<think>(.*?)</think>', response_with_reasoning, re.DOTALL)
    if think_match:
        thinking_content = think_match.group(1).strip()
        print(f"\n✓ Reasoning mode is WORKING!")
        print(f"  - Thinking content length: {len(thinking_content)} characters")
        print(f"  - First 200 chars of thinking: {thinking_content[:200]}...")
else:
    print(f"\n✗ Reasoning mode is NOT working - no <think> tags found")

print("\n" + "=" * 80)
