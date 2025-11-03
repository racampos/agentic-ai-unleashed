#!/usr/bin/env python3
"""
Test script for teaching nodes.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.nodes import teaching_retrieval_node, teaching_feedback_node


async def test_teaching_path():
    """Test the teaching nodes with a conceptual question."""

    question = "Why do we need the login keyword in line configuration mode?"

    print("=" * 80)
    print("TEACHING NODE TEST")
    print("=" * 80)
    print(f"\nQuestion: {question}\n")

    # Initial state
    state = {
        "student_question": question,
        "current_lab": None,  # Not lab-specific
        "mastery_level": "novice",
        "cli_history": []
    }

    # Step 1: Retrieval
    print("Step 1: Teaching Retrieval")
    print("-" * 80)
    retrieval_result = teaching_retrieval_node(state)
    state.update(retrieval_result)

    print(f"Retrieved {len(state['retrieved_docs'])} docs")
    if state['retrieved_docs']:
        print(f"First doc preview: {state['retrieved_docs'][0][:200]}...")

    # Step 2: Feedback
    print("\nStep 2: Teaching Feedback")
    print("-" * 80)
    feedback_result = await teaching_feedback_node(state)
    state.update(feedback_result)

    print(f"\n✅ Response ({len(state['feedback_message'])} chars):")
    print("-" * 80)
    print(state['feedback_message'])
    print("-" * 80)

    # Check quality
    response = state['feedback_message'].lower()
    has_conceptual = any(word in response for word in ['security', 'authentication', 'access', 'protect', 'verify'])
    no_cli_commands = 'login' not in response or 'password' in response  # Should explain, not just say "run login"

    print("\n📊 Quality Checks:")
    print(f"  Conceptual content: {'✅' if has_conceptual else '❌'}")
    print(f"  Not just CLI steps: {'✅' if no_cli_commands else '❌'}")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_teaching_path())
