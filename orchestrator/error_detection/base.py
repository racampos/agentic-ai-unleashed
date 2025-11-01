"""
Base classes and interfaces for error pattern detection.

This module provides the abstract base class for all error patterns,
defining the interface that all concrete pattern implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class DetectionResult:
    """
    Result of an error pattern detection attempt.

    Attributes:
        matched: Whether this pattern matched the error
        error_type: Type identifier for the error (e.g., "IPV6_PREFIX_SYNTAX")
        command: The actual command that was executed
        diagnosis: Educational explanation of what went wrong
        fix: Concrete steps to fix the error
        metadata: Additional context (mode, variables, etc.)
    """
    matched: bool
    error_type: Optional[str] = None
    command: Optional[str] = None
    diagnosis: Optional[str] = None
    fix: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage/serialization."""
        return {
            "type": self.error_type,
            "command": self.command,
            "diagnosis": self.diagnosis,
            "fix": self.fix,
            "metadata": self.metadata or {}
        }


class ErrorPattern(ABC):
    """
    Abstract base class for all error detection patterns.

    Each pattern represents a specific type of error that can occur
    in Cisco IOS CLI interactions. Patterns are checked in priority
    order, with higher priority patterns checked first.
    """

    def __init__(
        self,
        pattern_id: str,
        description: str,
        priority: int,
        error_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an error pattern.

        Args:
            pattern_id: Unique identifier for this pattern
            description: Human-readable description of the pattern
            priority: Detection priority (higher = checked first)
            error_type: Error type identifier (SCREAMING_SNAKE_CASE)
            metadata: Optional metadata (affected_modes, versions, etc.)
        """
        self.pattern_id = pattern_id
        self.description = description
        self.priority = priority
        self.error_type = error_type
        self.metadata = metadata or {}

    @abstractmethod
    def detect(self, command: str, output: str) -> DetectionResult:
        """
        Detect if this pattern matches the given command/output.

        Args:
            command: The CLI command that was executed
            output: The router's output/response

        Returns:
            DetectionResult with matched=True if pattern matches,
            matched=False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.pattern_id} (priority={self.priority})>"


class RegexErrorPattern(ErrorPattern):
    """
    Error pattern based on regex matching and signature detection.

    This is the most common pattern type, used for patterns loaded from
    JSON definitions. It matches based on:
    1. Signatures in the output (strings that must be present)
    2. Command regex pattern
    3. Optional marker position check (^ marker in IOS output)
    """

    def __init__(
        self,
        pattern_id: str,
        description: str,
        priority: int,
        signatures: List[str],
        command_pattern: Dict[str, Any],
        error_type: str,
        diagnosis_template: str,
        fix_template: str,
        diagnosis_variables: Optional[List[str]] = None,
        fix_examples: Optional[List[str]] = None,
        marker_check: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a regex-based error pattern.

        Args:
            pattern_id: Unique pattern identifier
            description: Human-readable description
            priority: Detection priority (higher = checked first)
            signatures: List of strings that must appear in output
            command_pattern: Dict with 'regex' and optional 'flags'
            error_type: Error type identifier
            diagnosis_template: Template string for diagnosis message
            fix_template: Template string for fix message
            diagnosis_variables: Variables to extract from regex matches
            fix_examples: Example fix commands
            marker_check: Optional dict with marker validation rules
            metadata: Additional metadata
        """
        super().__init__(pattern_id, description, priority, error_type, metadata)

        self.signatures = signatures
        self.diagnosis_template = diagnosis_template
        self.fix_template = fix_template
        self.diagnosis_variables = diagnosis_variables or []
        self.fix_examples = fix_examples or []
        self.marker_check = marker_check

        # Compile regex pattern
        flags = 0
        if command_pattern.get("flags") == "IGNORECASE":
            flags = re.IGNORECASE
        self.command_regex = re.compile(command_pattern["regex"], flags)

    def detect(self, command: str, output: str) -> DetectionResult:
        """
        Detect if this pattern matches the given command/output.

        Returns DetectionResult with matched=True if:
        1. All signatures are present in output
        2. Command matches the regex pattern
        3. Optional marker check passes (if enabled)
        """
        # Check if all signatures are present in output
        for signature in self.signatures:
            if signature not in output:
                return DetectionResult(matched=False)

        # Check if command matches the regex pattern
        match = self.command_regex.search(command)
        if not match:
            return DetectionResult(matched=False)

        # Optional: Check ^ marker position
        if self.marker_check and self.marker_check.get("enabled"):
            if not self._check_marker(output, match):
                return DetectionResult(matched=False)

        # Build diagnosis and fix messages
        variables = self._extract_variables(command, match)
        diagnosis = self._format_template(self.diagnosis_template, variables)
        fix = self._format_template(self.fix_template, variables)

        return DetectionResult(
            matched=True,
            error_type=self.error_type,
            command=command,
            diagnosis=diagnosis,
            fix=fix,
            metadata={
                **self.metadata,
                "pattern_id": self.pattern_id,
                "variables": variables
            }
        )

    def _extract_variables(self, command: str, match: re.Match) -> Dict[str, str]:
        """Extract variables from regex match groups."""
        variables = {"command": command}

        # Add named groups
        variables.update(match.groupdict())

        # Add indexed groups for diagnosis_variables
        for i, var_name in enumerate(self.diagnosis_variables, start=1):
            if i <= len(match.groups()):
                variables[var_name] = match.group(i)

        return variables

    def _format_template(self, template: str, variables: Dict[str, str]) -> str:
        """Format a template string with extracted variables."""
        try:
            return template.format(**variables)
        except KeyError as e:
            # Fallback if template variable is missing
            return template

    def _check_marker(self, output: str, match: re.Match) -> bool:
        """
        Check if ^ marker in output points to expected position.

        This is used to distinguish similar errors (e.g., typo vs syntax error).
        """
        if "^" not in output:
            return False

        expected_position = self.marker_check.get("expected_position")

        # Extract the line with the ^ marker
        marker_line_idx = -1
        for i, line in enumerate(output.split('\n')):
            if '^' in line:
                marker_line_idx = i
                break

        if marker_line_idx < 0:
            return False

        # Get the command line (usually right before the marker)
        lines = output.split('\n')
        if marker_line_idx == 0:
            return False

        marker_line = lines[marker_line_idx]
        marker_position = marker_line.index('^')

        # Check expected position
        if expected_position == "before_slash":
            # Marker should be near a / character
            return '/' in match.group(0)
        elif expected_position == "at_char":
            # Marker should point to specific character
            return True  # Basic validation, can be enhanced
        elif expected_position == "end_of_command":
            # Marker should be near end
            return marker_position > len(marker_line) * 0.7

        return True
