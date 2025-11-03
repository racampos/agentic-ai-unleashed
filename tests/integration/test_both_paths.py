#!/usr/bin/env python3
"""
Test script for both teaching and troubleshooting paths through the graph.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.graph import compile_graph


async def test_teaching_path():
    """Test a conceptual teaching question."""
    print("=" * 80)
    print("TEACHING PATH TEST")
    print("=" * 80)

    question = "Why do we need the login keyword in line configuration mode?"
    print(f"\nQuestion: {question}\n")

    state = {
        "student_question": question,
        "current_lab": None,
        "mastery_level": "novice",
        "cli_history": [],
        "conversation_history": [],
        "lab_objectives": ["Understand line configuration"],
        "completed_objectives": [],
        "hints_given": 0,
        "max_hints": 3,
        "success_rate": 0.0,
        "concepts_understood": [],
        "struggling_with": [],
        "total_interactions": 0,
        "tutoring_strategy": "socratic",
        "student_intent": "question",
    }

    graph = compile_graph()
    result = await graph.ainvoke(state)

    print(f"✅ Intent classified as: {result['intent']}")
    print(f"✅ Response ({len(result['feedback_message'])} chars):")
    print("-" * 80)
    print(result["feedback_message"])
    print("-" * 80)

    # Verify teaching path was used
    assert result['intent'] == 'teaching', f"Expected 'teaching', got '{result['intent']}'"
    assert 'retrieved_docs' in result, "Should have retrieved docs"
    assert len(result['feedback_message']) > 0, "Should have feedback"

    print("\n✅ Teaching path works!\n")


async def test_troubleshooting_path():
    """Test a troubleshooting question with CLI error."""
    print("=" * 80)
    print("TROUBLESHOOTING PATH TEST")
    print("=" * 80)

    question = "What did I do wrong?"
    cli_error = [
        {
            "command": "hostnane S1",
            "output": "Switch(config)#hostnane S1\n                     ^\n% Invalid input detected at '^' marker."
        }
    ]

    print(f"\nQuestion: {question}")
    print(f"CLI Error: hostnane S1\n")

    state = {
        "student_question": question,
        "current_lab": "01-basic-routing",
        "mastery_level": "novice",
        "cli_history": cli_error,
        "conversation_history": [],
        "lab_objectives": ["Configure hostname"],
        "completed_objectives": [],
        "hints_given": 0,
        "max_hints": 3,
        "success_rate": 0.0,
        "concepts_understood": [],
        "struggling_with": [],
        "total_interactions": 0,
        "tutoring_strategy": "socratic",
        "student_intent": "question",
    }

    graph = compile_graph()
    result = await graph.ainvoke(state)

    print(f"✅ Intent classified as: {result['intent']}")
    print(f"✅ Response ({len(result['feedback_message'])} chars):")
    print("-" * 80)
    print(result["feedback_message"])
    print("-" * 80)

    # Verify troubleshooting path was used
    assert result['intent'] == 'troubleshooting', f"Expected 'troubleshooting', got '{result['intent']}'"
    assert 'retrieved_docs' in result, "Should have retrieved docs"
    assert len(result['feedback_message']) > 0, "Should have feedback"

    # Check if typo was detected
    response_lower = result['feedback_message'].lower()
    if 'typo' in response_lower or 'hostname' in response_lower:
        print("\n✅ Typo detection working!")

    print("\n✅ Troubleshooting path works!\n")


async def main():
    """Run both path tests."""
    await test_teaching_path()
    await test_troubleshooting_path()

    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
