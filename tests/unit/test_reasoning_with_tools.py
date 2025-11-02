"""
Test if reasoning mode works when function calling is enabled.
"""

import os
from openai import OpenAI

api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("ERROR: NVIDIA_API_KEY environment variable not set")
    exit(1)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

# Define a simple tool
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

print("Testing reasoning mode WITH function calling enabled...")
print("=" * 80)

completion = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    messages=[
        {"role": "system", "content": "detailed thinking on"},
        {"role": "user", "content": "What's 2+2? Just answer the math question, don't use any tools."}
    ],
    tools=TOOLS,
    tool_choice="auto",
    temperature=0.6,
    top_p=0.95,
    max_tokens=2048,
)

response_content = completion.choices[0].message.content or ""
tool_calls = completion.choices[0].message.tool_calls

print(f"Response content:\n{response_content}\n")
print(f"Tool calls: {tool_calls}\n")
print(f"Contains <think> tags: {'<think>' in response_content}")

print("\n" + "=" * 80)
