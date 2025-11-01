"""
Main error detection orchestrator.

This module provides the high-level error detection interface that:
1. Runs patterns in priority order
2. Returns the first matching pattern
3. Provides batch detection for multiple commands
4. Supports optional filtering by error type or mode
"""

import logging
from typing import Optional, List, Dict, Any

from .base import ErrorPattern, DetectionResult
from .registry import PatternRegistry

logger = logging.getLogger(__name__)


class ErrorDetector:
    """
    Main error detection orchestrator.

    Coordinates pattern matching across all registered patterns,
    checking them in priority order and returning the first match.
    """

    def __init__(self, registry: PatternRegistry):
        """
        Initialize the error detector.

        Args:
            registry: PatternRegistry containing all available patterns
        """
        self.registry = registry
        self._patterns = registry.get_all_patterns()
        logger.info(f"ErrorDetector initialized with {len(self._patterns)} patterns")

    def detect(
        self,
        command: str,
        output: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[DetectionResult]:
        """
        Detect errors in a CLI command execution.

        Checks all registered patterns in priority order and returns
        the first match found.

        Args:
            command: The CLI command that was executed
            output: The router's output/response
            context: Optional context (current_mode, device_id, etc.)

        Returns:
            DetectionResult if an error is detected, None otherwise
        """
        context = context or {}

        logger.debug(f"Detecting errors for command: {command}")

        # Check patterns in priority order
        for pattern in self._patterns:
            logger.debug(f"Checking pattern: {pattern.pattern_id} (priority={pattern.priority})")

            # Optional: Filter by affected_modes if context provides current_mode
            if context.get("current_mode"):
                affected_modes = pattern.metadata.get("affected_modes", [])
                if affected_modes and context["current_mode"] not in affected_modes:
                    logger.debug(f"Skipping pattern {pattern.pattern_id}: mode mismatch")
                    continue

            # Run pattern detection
            result = pattern.detect(command, output)

            if result.matched:
                logger.info(
                    f"Pattern matched: {pattern.pattern_id} (type={result.error_type})"
                )
                return result

        logger.debug("No patterns matched")
        return None

    def detect_batch(
        self,
        commands: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Optional[DetectionResult]]:
        """
        Detect errors for multiple commands.

        Args:
            commands: List of dicts with 'command' and 'output' keys
            context: Optional context shared across all commands

        Returns:
            List of DetectionResult (or None) for each command
        """
        results = []
        for cmd_data in commands:
            result = self.detect(
                cmd_data["command"],
                cmd_data["output"],
                context
            )
            results.append(result)
        return results

    def get_patterns_by_type(self, error_type: str) -> List[ErrorPattern]:
        """
        Get all patterns that detect a specific error type.

        Args:
            error_type: Error type identifier (e.g., "WRONG_MODE")

        Returns:
            List of matching patterns
        """
        return [
            pattern for pattern in self._patterns
            if pattern.error_type == error_type
        ]

    def get_patterns_by_priority(self, min_priority: int) -> List[ErrorPattern]:
        """
        Get all patterns with priority >= min_priority.

        Args:
            min_priority: Minimum priority threshold

        Returns:
            List of patterns with sufficient priority
        """
        return [
            pattern for pattern in self._patterns
            if pattern.priority >= min_priority
        ]

    def reload_patterns(self) -> None:
        """
        Reload patterns from the registry.

        Useful if patterns are added/removed dynamically.
        """
        self._patterns = self.registry.get_all_patterns()
        logger.info(f"Reloaded {len(self._patterns)} patterns")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get detector statistics.

        Returns:
            Dictionary with stats (pattern count, types, priorities)
        """
        error_types = {}
        for pattern in self._patterns:
            error_type = pattern.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_patterns": len(self._patterns),
            "error_types": error_types,
            "registry_stats": self.registry.get_stats(),
        }


# Helper function to convert DetectionResult to dictionary format
# compatible with the existing POC code
def detection_result_to_dict(result: Optional[DetectionResult]) -> Optional[Dict[str, Any]]:
    """
    Convert DetectionResult to dictionary format.

    Args:
        result: DetectionResult or None

    Returns:
        Dictionary with error info, or None if no detection
    """
    if result is None or not result.matched:
        return None

    return result.to_dict()
