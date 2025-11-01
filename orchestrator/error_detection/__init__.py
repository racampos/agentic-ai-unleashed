"""
Error Detection Framework for Cisco IOS CLI Analysis

This module provides a modular, pattern-based error detection system
for identifying and diagnosing common Cisco IOS configuration errors.

Public API:
    - ErrorDetector: Main detection orchestrator
    - PatternRegistry: Registry for managing patterns
    - load_default_patterns: Load patterns from default locations
    - detection_result_to_dict: Convert results to dict format

Usage:
    from orchestrator.error_detection import get_default_detector

    detector = get_default_detector()
    result = detector.detect(command="hostname Router1", output="Router#hostname...")

    if result:
        print(f"Error detected: {result.error_type}")
        print(f"Diagnosis: {result.diagnosis}")
        print(f"Fix: {result.fix}")
"""

import logging
from typing import Optional

from .base import ErrorPattern, RegexErrorPattern, FuzzyErrorPattern, DetectionResult
from .registry import PatternRegistry, load_default_patterns
from .detector import ErrorDetector, detection_result_to_dict

logger = logging.getLogger(__name__)

# Global singleton detector instance
_default_detector: Optional[ErrorDetector] = None


def get_default_detector() -> ErrorDetector:
    """
    Get the default error detector instance.

    Lazily initializes the detector on first call by loading
    patterns from default locations.

    Returns:
        ErrorDetector instance with all loaded patterns
    """
    global _default_detector

    if _default_detector is None:
        logger.info("Initializing default error detector")
        registry = load_default_patterns()
        _default_detector = ErrorDetector(registry)

    return _default_detector


def reload_default_detector() -> ErrorDetector:
    """
    Reload the default detector with fresh patterns.

    Useful for development or when pattern files are updated.

    Returns:
        New ErrorDetector instance
    """
    global _default_detector

    logger.info("Reloading default error detector")
    registry = load_default_patterns()
    _default_detector = ErrorDetector(registry)

    return _default_detector


# Public exports
__all__ = [
    # Base classes
    "ErrorPattern",
    "RegexErrorPattern",
    "FuzzyErrorPattern",
    "DetectionResult",

    # Registry
    "PatternRegistry",
    "load_default_patterns",

    # Detector
    "ErrorDetector",
    "detection_result_to_dict",

    # Convenience functions
    "get_default_detector",
    "reload_default_detector",
]
