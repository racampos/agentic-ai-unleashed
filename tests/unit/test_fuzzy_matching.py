#!/usr/bin/env python3
"""
Test script for fuzzy matching typo detection.

Tests the new FuzzyErrorPattern functionality with real examples.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.error_detection import get_default_detector, reload_default_detector

def test_hostname_typo():
    """Test the exact example from the user: hostnane S1"""
    print("=" * 70)
    print("TEST 1: Hostname typo detection (hostnane -> hostname)")
    print("=" * 70)

    command = "hostnane S1"
    output = """Switch(config)#hostnane S1
                     ^
% Invalid input detected at '^' marker.

Switch(config)#"""

    detector = reload_default_detector()
    result = detector.detect(command, output)

    if result:
        print(f"✅ Error detected: {result.error_type}")
        print(f"\n📋 Diagnosis:\n{result.diagnosis}")
        print(f"\n🔧 Fix:\n{result.fix}")

        if result.metadata.get("typo_detected"):
            print(f"\n🎯 Typo Details:")
            print(f"   - Typo word: {result.metadata.get('typo_word')}")
            print(f"   - Suggested: {result.metadata.get('suggested_word')}")
            print(f"   - Similarity: {result.metadata.get('similarity_score'):.0%}")
            print(f"   - Corrected: {result.metadata.get('corrected_command')}")
            return True
        else:
            print("\n❌ Typo not specifically detected!")
            return False
    else:
        print("❌ No error detected!")
        return False


def test_interface_typo():
    """Test interface misspelling: interfase -> interface"""
    print("\n" + "=" * 70)
    print("TEST 2: Interface typo detection (interfase -> interface)")
    print("=" * 70)

    command = "interfase g0/0"
    output = """Switch(config)#interfase g0/0
                ^
% Invalid input detected at '^' marker.

Switch(config)#"""

    detector = get_default_detector()
    result = detector.detect(command, output)

    if result:
        print(f"✅ Error detected: {result.error_type}")

        if result.metadata.get("typo_detected"):
            print(f"\n🎯 Typo Details:")
            print(f"   - Typo word: {result.metadata.get('typo_word')}")
            print(f"   - Suggested: {result.metadata.get('suggested_word')}")
            print(f"   - Similarity: {result.metadata.get('similarity_score'):.0%}")
            return True
        else:
            print("\n❌ Typo not specifically detected!")
            return False
    else:
        print("❌ No error detected!")
        return False


def test_configure_typo():
    """Test configure misspelling: cofigure -> configure"""
    print("\n" + "=" * 70)
    print("TEST 3: Configure typo detection (cofigure -> configure)")
    print("=" * 70)

    command = "cofigure terminal"
    output = """Switch#cofigure terminal
       ^
% Invalid input detected at '^' marker.

Switch#"""

    detector = get_default_detector()
    result = detector.detect(command, output)

    if result:
        print(f"✅ Error detected: {result.error_type}")

        if result.metadata.get("typo_detected"):
            print(f"\n🎯 Typo Details:")
            print(f"   - Typo word: {result.metadata.get('typo_word')}")
            print(f"   - Suggested: {result.metadata.get('suggested_word')}")
            print(f"   - Similarity: {result.metadata.get('similarity_score'):.0%}")
            return True
        else:
            print("\n❌ Typo not specifically detected!")
            return False
    else:
        print("❌ No error detected!")
        return False


def test_no_false_positives():
    """Test that valid commands don't trigger false positives"""
    print("\n" + "=" * 70)
    print("TEST 4: No false positives on valid commands")
    print("=" * 70)

    command = "show running-config"
    output = """Switch#show running-config
Building configuration...

Current configuration : 1234 bytes
!
version 15.2
!"""

    detector = get_default_detector()
    result = detector.detect(command, output)

    if result:
        print(f"❌ False positive! Error detected: {result.error_type}")
        return False
    else:
        print("✅ No error detected (correct)")
        return True


def main():
    """Run all tests"""
    print("\n🧪 FUZZY MATCHING TYPO DETECTION TEST SUITE\n")

    results = []
    results.append(("Hostname typo", test_hostname_typo()))
    results.append(("Interface typo", test_interface_typo()))
    results.append(("Configure typo", test_configure_typo()))
    results.append(("No false positives", test_no_false_positives()))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
