"""
Pattern registry and JSON loader for error detection patterns.

This module provides functionality to:
1. Load error patterns from JSON files
2. Validate pattern definitions
3. Maintain a registry of all available patterns
4. Support both generated patterns and hardcoded patterns
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import ErrorPattern, RegexErrorPattern

logger = logging.getLogger(__name__)


class PatternValidationError(Exception):
    """Raised when a pattern definition fails validation."""
    pass


class PatternRegistry:
    """
    Registry for all error detection patterns.

    Manages loading, validation, and retrieval of error patterns
    from both JSON files and programmatically defined patterns.
    """

    def __init__(self):
        """Initialize an empty pattern registry."""
        self._patterns: List[ErrorPattern] = []
        self._patterns_by_id: Dict[str, ErrorPattern] = {}

    def load_from_json(self, json_path: Path) -> int:
        """
        Load patterns from a JSON file.

        Args:
            json_path: Path to JSON file containing pattern definitions

        Returns:
            Number of patterns loaded

        Raises:
            PatternValidationError: If JSON is invalid or patterns fail validation
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise PatternValidationError(f"Invalid JSON in {json_path}: {e}")
        except FileNotFoundError:
            logger.warning(f"Pattern file not found: {json_path}")
            return 0

        # Validate top-level structure
        if not isinstance(data, dict):
            raise PatternValidationError("JSON root must be an object")

        if "patterns" not in data:
            raise PatternValidationError("JSON must contain 'patterns' array")

        patterns_data = data["patterns"]
        if not isinstance(patterns_data, list):
            raise PatternValidationError("'patterns' must be an array")

        # Load each pattern
        loaded_count = 0
        for i, pattern_def in enumerate(patterns_data):
            try:
                pattern = self._load_pattern_from_dict(pattern_def)
                self.register(pattern)
                loaded_count += 1
            except PatternValidationError as e:
                logger.error(f"Failed to load pattern #{i} from {json_path}: {e}")
                # Continue loading other patterns

        logger.info(f"Loaded {loaded_count} patterns from {json_path}")
        return loaded_count

    def _load_pattern_from_dict(self, pattern_def: Dict[str, Any]) -> ErrorPattern:
        """
        Load a single pattern from a dictionary definition.

        Args:
            pattern_def: Dictionary containing pattern definition

        Returns:
            Constructed ErrorPattern instance

        Raises:
            PatternValidationError: If pattern definition is invalid
        """
        # Validate required fields
        required_fields = [
            "pattern_id", "description", "priority", "signatures",
            "command_pattern", "error_type", "diagnosis", "fix"
        ]

        for field in required_fields:
            if field not in pattern_def:
                raise PatternValidationError(f"Missing required field: {field}")

        # Validate types
        if not isinstance(pattern_def["pattern_id"], str):
            raise PatternValidationError("pattern_id must be a string")

        if not isinstance(pattern_def["priority"], int):
            raise PatternValidationError("priority must be an integer")

        if not isinstance(pattern_def["signatures"], list):
            raise PatternValidationError("signatures must be an array")

        if not isinstance(pattern_def["command_pattern"], dict):
            raise PatternValidationError("command_pattern must be an object")

        if "regex" not in pattern_def["command_pattern"]:
            raise PatternValidationError("command_pattern must contain 'regex' field")

        # Extract diagnosis fields
        diagnosis = pattern_def["diagnosis"]
        if isinstance(diagnosis, dict):
            diagnosis_template = diagnosis.get("template", "")
            diagnosis_variables = diagnosis.get("variables", [])
        elif isinstance(diagnosis, str):
            # Legacy format - just a string
            diagnosis_template = diagnosis
            diagnosis_variables = []
        else:
            raise PatternValidationError("diagnosis must be object or string")

        # Extract fix fields
        fix = pattern_def["fix"]
        if isinstance(fix, dict):
            fix_template = fix.get("template", "")
            fix_examples = fix.get("examples", [])
        elif isinstance(fix, str):
            # Legacy format - just a string
            fix_template = fix
            fix_examples = []
        else:
            raise PatternValidationError("fix must be object or string")

        # Create RegexErrorPattern instance
        pattern = RegexErrorPattern(
            pattern_id=pattern_def["pattern_id"],
            description=pattern_def["description"],
            priority=pattern_def["priority"],
            signatures=pattern_def["signatures"],
            command_pattern=pattern_def["command_pattern"],
            error_type=pattern_def["error_type"],
            diagnosis_template=diagnosis_template,
            fix_template=fix_template,
            diagnosis_variables=diagnosis_variables,
            fix_examples=fix_examples,
            marker_check=pattern_def.get("marker_check"),
            metadata=pattern_def.get("metadata", {})
        )

        return pattern

    def register(self, pattern: ErrorPattern) -> None:
        """
        Register a pattern in the registry.

        Args:
            pattern: ErrorPattern instance to register

        Raises:
            PatternValidationError: If pattern_id already exists
        """
        if pattern.pattern_id in self._patterns_by_id:
            raise PatternValidationError(
                f"Pattern with id '{pattern.pattern_id}' already registered"
            )

        self._patterns.append(pattern)
        self._patterns_by_id[pattern.pattern_id] = pattern

        # Keep patterns sorted by priority (highest first)
        self._patterns.sort(key=lambda p: p.priority, reverse=True)

        logger.debug(f"Registered pattern: {pattern}")

    def get_all_patterns(self) -> List[ErrorPattern]:
        """
        Get all registered patterns in priority order.

        Returns:
            List of ErrorPattern instances, sorted by priority (highest first)
        """
        return self._patterns.copy()

    def get_pattern_by_id(self, pattern_id: str) -> Optional[ErrorPattern]:
        """
        Get a specific pattern by its ID.

        Args:
            pattern_id: Unique pattern identifier

        Returns:
            ErrorPattern instance or None if not found
        """
        return self._patterns_by_id.get(pattern_id)

    def clear(self) -> None:
        """Clear all registered patterns."""
        self._patterns.clear()
        self._patterns_by_id.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats (count, priorities, etc.)
        """
        return {
            "total_patterns": len(self._patterns),
            "pattern_ids": [p.pattern_id for p in self._patterns],
            "priority_distribution": self._get_priority_distribution(),
        }

    def _get_priority_distribution(self) -> Dict[int, int]:
        """Get distribution of patterns by priority level."""
        distribution: Dict[int, int] = {}
        for pattern in self._patterns:
            distribution[pattern.priority] = distribution.get(pattern.priority, 0) + 1
        return distribution


def load_default_patterns() -> PatternRegistry:
    """
    Load patterns from the default locations.

    Looks for patterns in:
    1. orchestrator/error_detection/patterns/generated/patterns.json (LLM-generated)
    2. orchestrator/error_detection/patterns/hardcoded.json (manually defined)

    Returns:
        PatternRegistry with all loaded patterns
    """
    registry = PatternRegistry()

    # Get base directory (orchestrator/error_detection)
    base_dir = Path(__file__).parent

    # Load generated patterns
    generated_path = base_dir / "patterns" / "generated" / "patterns.json"
    if generated_path.exists():
        try:
            count = registry.load_from_json(generated_path)
            logger.info(f"Loaded {count} generated patterns from {generated_path}")
        except PatternValidationError as e:
            logger.error(f"Failed to load generated patterns: {e}")

    # Load hardcoded patterns
    hardcoded_path = base_dir / "patterns" / "hardcoded.json"
    if hardcoded_path.exists():
        try:
            count = registry.load_from_json(hardcoded_path)
            logger.info(f"Loaded {count} hardcoded patterns from {hardcoded_path}")
        except PatternValidationError as e:
            logger.error(f"Failed to load hardcoded patterns: {e}")

    logger.info(f"Pattern registry initialized with {len(registry.get_all_patterns())} total patterns")
    return registry
