#!/usr/bin/env python3
"""
Test script for intent classification.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.nodes import intent_router_node

def test_intent(question, expected=None, cli_history=None):
    """Test a single question and print classification."""
    state = {
        "student_question": question,
        "cli_history": cli_history or []
    }

    result = intent_router_node(state)
    intent = result["intent"]

    status = "✅" if expected is None or intent == expected else "❌"
    print(f"{status} {intent:15s} | {question[:60]}")

    return intent == expected if expected else True


def main():
    print("=" * 80)
    print("INTENT CLASSIFICATION TEST")
    print("=" * 80)

    print("\n🎓 Teaching Questions (should classify as 'teaching'):")
    test_intent("Why do we need the login keyword?", "teaching")
    test_intent("What is the difference between enable and enable secret?", "teaching")
    test_intent("Explain how VLANs work", "teaching")
    test_intent("What does the configure terminal command do?", "teaching")
    test_intent("When should I use static routing vs dynamic routing?", "teaching")
    test_intent("What are the benefits of using SSH instead of Telnet?", "teaching")
    test_intent("Purpose of the subnet mask?", "teaching")

    print("\n🔧 Troubleshooting Questions (should classify as 'troubleshooting'):")
    test_intent("What did I do wrong?", "troubleshooting")
    test_intent("Why is this command not working?", "troubleshooting")
    test_intent("How do I fix this error?", "troubleshooting")
    test_intent("Something is broken, help!", "troubleshooting")
    test_intent("I'm stuck, what's the problem?", "troubleshooting")
    test_intent("Why isn't my configuration working?", "troubleshooting")

    print("\n⚠️  With CLI Errors (should be troubleshooting):")
    error_cli = [
        {
            "command": "hostnane S1",
            "output": "Switch(config)#hostnane S1\n                     ^\n% Invalid input detected at '^' marker."
        }
    ]
    test_intent("What's wrong?", "troubleshooting", error_cli)
    test_intent("Why do we need the login keyword?", "teaching", error_cli)  # Teaching even with errors

    print("\n🤔 Ambiguous (defaults to 'teaching'):")
    test_intent("Tell me more", "teaching")
    test_intent("What about this?", "teaching")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
