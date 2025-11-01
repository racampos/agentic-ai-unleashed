#!/usr/bin/env python3
"""
Quick test script to verify the error detection framework works.
"""

import sys
sys.path.append('.')

from orchestrator.error_detection import get_default_detector

def test_wrong_mode():
    """Test the WRONG_MODE pattern from hardcoded.json."""
    detector = get_default_detector()

    # Test case: hostname command in privileged exec mode
    command = "hostname Router123"
    output = """Floor14#hostname Router123
        ^
% Invalid input detected at '^' marker.
Floor14#"""

    print("=" * 60)
    print("Testing WRONG_MODE pattern")
    print("=" * 60)
    print(f"Command: {command}")
    print(f"Output:\n{output}")
    print()

    result = detector.detect(command, output)

    if result:
        print("✓ Error detected!")
        print(f"  Type: {result.error_type}")
        print(f"  Diagnosis: {result.diagnosis}")
        print(f"  Fix: {result.fix}")
    else:
        print("✗ No error detected (unexpected)")

    print()
    return result is not None


def test_interface_mode():
    """Test the interface config mode pattern."""
    detector = get_default_detector()

    # Test case: ip address command in privileged exec mode
    command = "ip address 192.168.1.1 255.255.255.0"
    output = """Floor14#ip address 192.168.1.1 255.255.255.0
           ^
% Invalid input detected at '^' marker.
Floor14#"""

    print("=" * 60)
    print("Testing WRONG_MODE pattern (interface commands)")
    print("=" * 60)
    print(f"Command: {command}")
    print(f"Output:\n{output}")
    print()

    result = detector.detect(command, output)

    if result:
        print("✓ Error detected!")
        print(f"  Type: {result.error_type}")
        print(f"  Diagnosis: {result.diagnosis}")
        print(f"  Fix: {result.fix}")
    else:
        print("✗ No error detected (unexpected)")

    print()
    return result is not None


def test_no_error():
    """Test that valid commands don't trigger false positives."""
    detector = get_default_detector()

    # Test case: successful command
    command = "show ip interface brief"
    output = """Floor14#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     unassigned      YES unset  administratively down down
GigabitEthernet0/1     unassigned      YES unset  administratively down down
Floor14#"""

    print("=" * 60)
    print("Testing no false positives")
    print("=" * 60)
    print(f"Command: {command}")
    print()

    result = detector.detect(command, output)

    if result:
        print("✗ False positive detected (unexpected)")
        print(f"  Type: {result.error_type}")
    else:
        print("✓ No error detected (correct)")

    print()
    return result is None


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Error Detection Framework Test Suite")
    print("=" * 60)
    print()

    # Get detector stats
    detector = get_default_detector()
    stats = detector.get_stats()

    print("Framework loaded successfully!")
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Error types: {list(stats['error_types'].keys())}")
    print()

    # Run tests
    results = []
    results.append(("WRONG_MODE test", test_wrong_mode()))
    results.append(("Interface mode test", test_interface_mode()))
    results.append(("No false positives test", test_no_error()))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Passed: {passed}/{total}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
