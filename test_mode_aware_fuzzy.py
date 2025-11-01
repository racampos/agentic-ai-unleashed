#!/usr/bin/env python3
"""
Test mode-aware fuzzy matching.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.error_detection import reload_default_detector

def test_loggin_in_line_mode():
    """Test the user's exact example: loggin in line config mode"""
    print("=" * 70)
    print("TEST: loggin -> login (in line config mode)")
    print("=" * 70)

    command = "loggin"
    output = """MySwitch(config-line)#loggin
                         ^
% Invalid input detected at '^' marker.

MySwitch(config-line)#"""

    detector = reload_default_detector()
    result = detector.detect(command, output)

    if result:
        print(f"✅ Error detected: {result.error_type}")
        print(f"\n📋 Diagnosis:\n{result.diagnosis}")
        print(f"\n🔧 Fix:\n{result.fix}")

        if result.metadata.get("typo_detected"):
            typo_word = result.metadata.get('typo_word')
            suggested = result.metadata.get('suggested_word')
            print(f"\n🎯 Typo Details:")
            print(f"   - Typo word: {typo_word}")
            print(f"   - Suggested: {suggested}")
            print(f"   - Similarity: {result.metadata.get('similarity_score'):.0%}")

            if suggested == "login":
                print(f"\n✅ CORRECT! Suggested 'login' not 'logging'")
                return True
            else:
                print(f"\n❌ WRONG! Suggested '{suggested}' instead of 'login'")
                return False
        else:
            print("\n❌ Typo not detected!")
            return False
    else:
        print("❌ No error detected!")
        return False


def test_hostnane_in_global_config():
    """Test mode awareness doesn't break existing tests"""
    print("\n" + "=" * 70)
    print("TEST: hostnane -> hostname (in global config mode)")
    print("=" * 70)

    command = "hostnane S1"
    output = """Switch(config)#hostnane S1
                     ^
% Invalid input detected at '^' marker.

Switch(config)#"""

    detector = reload_default_detector()
    result = detector.detect(command, output)

    if result and result.metadata.get("typo_detected"):
        suggested = result.metadata.get('suggested_word')
        print(f"✅ Suggested: {suggested}")
        return suggested == "hostname"

    print("❌ Failed")
    return False


if __name__ == "__main__":
    results = []
    results.append(("loggin -> login (line config)", test_loggin_in_line_mode()))
    results.append(("hostnane -> hostname (global config)", test_hostnane_in_global_config()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")

    sys.exit(0 if all(p for _, p in results) else 1)
