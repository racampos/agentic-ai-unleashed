"""
Test utilities for error detection patterns.

Provides simple validation and testing for pattern definitions.
"""

import logging
from typing import List, Dict, Any, Tuple

from .base import ErrorPattern, DetectionResult
from .detector import ErrorDetector

logger = logging.getLogger(__name__)


class PatternTester:
    """
    Utility for testing error detection patterns.

    Provides methods to validate patterns against test cases
    and verify that patterns produce expected results.
    """

    def __init__(self, detector: ErrorDetector):
        """
        Initialize the pattern tester.

        Args:
            detector: ErrorDetector instance to test
        """
        self.detector = detector

    def test_pattern(
        self,
        pattern_id: str,
        test_cases: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[str]]:
        """
        Test a specific pattern against test cases.

        Args:
            pattern_id: ID of pattern to test
            test_cases: List of test case dicts with:
                - command: CLI command to test
                - output: Router output
                - should_match: Whether pattern should match
                - expected_type: Expected error type (if should_match)

        Returns:
            Tuple of (passed_count, failed_count, failure_messages)
        """
        pattern = self.detector.registry.get_pattern_by_id(pattern_id)
        if not pattern:
            return 0, len(test_cases), [f"Pattern '{pattern_id}' not found"]

        passed = 0
        failed = 0
        failures = []

        for i, test_case in enumerate(test_cases):
            command = test_case["command"]
            output = test_case["output"]
            should_match = test_case.get("should_match", True)
            expected_type = test_case.get("expected_type")

            result = pattern.detect(command, output)

            # Check if match expectation is met
            if should_match and not result.matched:
                failed += 1
                failures.append(
                    f"Test case #{i}: Expected match but pattern didn't match\n"
                    f"  Command: {command}\n"
                    f"  Output: {output[:100]}..."
                )
            elif not should_match and result.matched:
                failed += 1
                failures.append(
                    f"Test case #{i}: Expected no match but pattern matched\n"
                    f"  Command: {command}\n"
                    f"  Type: {result.error_type}"
                )
            elif should_match and result.matched:
                # Check error type if specified
                if expected_type and result.error_type != expected_type:
                    failed += 1
                    failures.append(
                        f"Test case #{i}: Error type mismatch\n"
                        f"  Expected: {expected_type}\n"
                        f"  Got: {result.error_type}"
                    )
                else:
                    passed += 1
            else:
                passed += 1

        return passed, failed, failures

    def test_detector(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[str]]:
        """
        Test the entire detector against test cases.

        Similar to test_pattern but tests the full detection flow
        (all patterns in priority order).

        Args:
            test_cases: List of test case dicts

        Returns:
            Tuple of (passed_count, failed_count, failure_messages)
        """
        passed = 0
        failed = 0
        failures = []

        for i, test_case in enumerate(test_cases):
            command = test_case["command"]
            output = test_case["output"]
            should_detect = test_case.get("should_detect", True)
            expected_type = test_case.get("expected_type")

            result = self.detector.detect(command, output)

            if should_detect and not result:
                failed += 1
                failures.append(
                    f"Test case #{i}: Expected error detection but nothing detected\n"
                    f"  Command: {command}\n"
                    f"  Output: {output[:100]}..."
                )
            elif not should_detect and result:
                failed += 1
                failures.append(
                    f"Test case #{i}: Expected no detection but error detected\n"
                    f"  Command: {command}\n"
                    f"  Type: {result.error_type}"
                )
            elif should_detect and result:
                # Check error type if specified
                if expected_type and result.error_type != expected_type:
                    failed += 1
                    failures.append(
                        f"Test case #{i}: Error type mismatch\n"
                        f"  Expected: {expected_type}\n"
                        f"  Got: {result.error_type}"
                    )
                else:
                    passed += 1
            else:
                passed += 1

        return passed, failed, failures

    def print_test_results(
        self,
        name: str,
        passed: int,
        failed: int,
        failures: List[str]
    ) -> None:
        """
        Print formatted test results.

        Args:
            name: Name of the test suite
            passed: Number of passed tests
            failed: Number of failed tests
            failures: List of failure messages
        """
        total = passed + failed
        print(f"\n{'='*60}")
        print(f"Test Results: {name}")
        print(f"{'='*60}")
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {failed}/{total}")

        if failures:
            print(f"\n{'='*60}")
            print("Failures:")
            print(f"{'='*60}")
            for failure in failures:
                print(f"\n{failure}")

        if failed == 0:
            print(f"\n✓ All tests passed!")
        else:
            print(f"\n✗ {failed} test(s) failed")


def validate_json_patterns(json_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a JSON pattern file without loading into registry.

    Args:
        json_path: Path to JSON pattern file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    import json
    from pathlib import Path

    errors = []

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return False, [f"File not found: {json_path}"]

    # Check top-level structure
    if not isinstance(data, dict):
        errors.append("JSON root must be an object")
        return False, errors

    if "patterns" not in data:
        errors.append("Missing 'patterns' array")
        return False, errors

    patterns = data["patterns"]
    if not isinstance(patterns, list):
        errors.append("'patterns' must be an array")
        return False, errors

    # Validate each pattern
    required_fields = [
        "pattern_id", "description", "priority", "signatures",
        "command_pattern", "error_type", "diagnosis", "fix"
    ]

    for i, pattern in enumerate(patterns):
        pattern_errors = []

        # Check required fields
        for field in required_fields:
            if field not in pattern:
                pattern_errors.append(f"Missing field: {field}")

        # Check types
        if "priority" in pattern and not isinstance(pattern["priority"], int):
            pattern_errors.append("'priority' must be an integer")

        if "signatures" in pattern and not isinstance(pattern["signatures"], list):
            pattern_errors.append("'signatures' must be an array")

        if "command_pattern" in pattern:
            if not isinstance(pattern["command_pattern"], dict):
                pattern_errors.append("'command_pattern' must be an object")
            elif "regex" not in pattern["command_pattern"]:
                pattern_errors.append("'command_pattern' must have 'regex' field")

        if pattern_errors:
            errors.append(f"Pattern #{i} ({pattern.get('pattern_id', 'unknown')}):")
            errors.extend([f"  - {err}" for err in pattern_errors])

    is_valid = len(errors) == 0
    return is_valid, errors
