"""
Test script for the streaming chat endpoint.

This script tests the /api/chat/stream endpoint to verify that
responses stream correctly using Server-Sent Events (SSE).
"""

import httpx
import json

# Configuration
BASE_URL = "http://localhost:8888"
SESSION_ID = "test-session-123"

def test_streaming():
    """Test the streaming chat endpoint."""

    print("Testing streaming chat endpoint...")
    print("=" * 80)

    # Create a chat request
    request_data = {
        "session_id": SESSION_ID,
        "message": "What's the IP address for my Gig 0/0 interface?",
        "cli_history": []
    }

    # Make the streaming request
    with httpx.stream(
        "POST",
        f"{BASE_URL}/api/chat/stream",
        json=request_data,
        timeout=30.0
    ) as response:
        print(f"Response status: {response.status_code}\n")

        if response.status_code != 200:
            print(f"Error: {response.text}")
            return

        print("Streaming response:")
        print("-" * 80)

        # Process SSE stream
        for line in response.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                try:
                    data = json.loads(data_str)

                    if data.get("type") == "content":
                        # Print content chunks without newline
                        print(data["text"], end="", flush=True)
                    elif data.get("type") == "metadata":
                        print("\n\n" + "=" * 80)
                        print("Metadata:")
                        print(json.dumps(data, indent=2))
                    elif data.get("type") == "done":
                        print("\n\n" + "=" * 80)
                        print("Stream complete!")
                    elif data.get("type") == "error":
                        print(f"\n\nError: {data.get('message')}")

                except json.JSONDecodeError:
                    print(f"\nFailed to parse: {data_str}")

if __name__ == "__main__":
    test_streaming()
