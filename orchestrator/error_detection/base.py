"""
Base classes and interfaces for error pattern detection.

This module provides the abstract base class for all error patterns,
defining the interface that all concrete pattern implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re
import json
import difflib
from pathlib import Path


# Global cache for command vocabulary
_COMMAND_VOCAB_CACHE: Optional[List[str]] = None


def load_command_vocabulary() -> List[str]:
    """
    Load the Cisco IOS command vocabulary for fuzzy matching.

    Returns:
        List of valid Cisco IOS command keywords
    """
    global _COMMAND_VOCAB_CACHE

    if _COMMAND_VOCAB_CACHE is not None:
        return _COMMAND_VOCAB_CACHE

    vocab_path = Path(__file__).parent / "cisco_commands.json"

    try:
        with open(vocab_path, 'r') as f:
            data = json.load(f)

        # Flatten all commands from all modes into a single list
        all_commands = []
        for mode_commands in data.get("commands", {}).values():
            all_commands.extend(mode_commands)

        # Remove duplicates and sort
        _COMMAND_VOCAB_CACHE = sorted(set(all_commands))
        return _COMMAND_VOCAB_CACHE

    except Exception as e:
        # If loading fails, return a minimal vocabulary
        return ["hostname", "interface", "ip", "address", "enable", "configure",
                "terminal", "show", "running-config", "password", "secret"]


def extract_word_at_marker(command: str, output: str) -> Optional[Tuple[str, int]]:
    """
    Extract the word that the ^ marker is pointing to in Cisco error output.

    Args:
        command: The CLI command that was executed
        output: The router's error output containing the ^ marker

    Returns:
        Tuple of (word, word_index) if found, None otherwise

    Example:
        >>> command = "hostnane S1"
        >>> output = "Switch(config)#hostnane S1\\n                     ^\\n% Invalid input..."
        >>> extract_word_at_marker(command, output)
        ('hostnane', 0)
    """
    if "^" not in output:
        return None

    # Find the line with the ^ marker
    lines = output.split('\n')
    marker_line_idx = -1
    for i, line in enumerate(lines):
        if '^' in line:
            marker_line_idx = i
            break

    if marker_line_idx < 0 or marker_line_idx == 0:
        return None

    # Get the command line (right before the marker)
    command_line = lines[marker_line_idx - 1]
    marker_line = lines[marker_line_idx]

    # Find the position of the ^ marker
    marker_position = marker_line.index('^')

    # Extract just the command part (after the prompt)
    # Cisco prompts end with # or >, find the last one
    prompt_end = max(command_line.rfind('#'), command_line.rfind('>'))
    if prompt_end < 0:
        # No prompt found, use the whole line
        command_part = command_line
        offset = 0
    else:
        command_part = command_line[prompt_end + 1:]
        offset = prompt_end + 1

    # Adjust marker position relative to command start
    adjusted_marker = marker_position - offset

    if adjusted_marker < 0 or adjusted_marker >= len(command_part):
        return None

    # Split command into words and find which word the marker points to
    words = command_part.split()
    current_pos = 0

    for word_idx, word in enumerate(words):
        word_start = command_part.find(word, current_pos)
        word_end = word_start + len(word)

        # Check if marker is within this word
        if word_start <= adjusted_marker < word_end:
            return (word, word_idx)

        current_pos = word_end

    # Marker might be pointing to whitespace or end, return last word
    if words:
        return (words[-1], len(words) - 1)

    return None


def detect_cisco_mode(output: str) -> Optional[str]:
    """
    Detect the current Cisco IOS mode from error output.

    Args:
        output: The router's error output containing the prompt

    Returns:
        Mode identifier string or None if not detected

    Mode mappings:
        - "(config)#" -> "global_config"
        - "(config-if)#" -> "interface_config"
        - "(config-line)#" -> "line_config"
        - "(config-router)#" -> "router_config"
        - "#" (privileged exec) -> "exec_mode"
        - ">" (user exec) -> "exec_mode"
    """
    # Look for mode indicators in the output
    if "(config-line)#" in output:
        return "line_config"
    elif "(config-if)#" in output:
        return "interface_config"
    elif "(config-router)#" in output:
        return "router_config"
    elif "(config" in output and ")#" in output:
        # Generic config mode, treat as global_config
        return "global_config"
    elif "#" in output or ">" in output:
        return "exec_mode"

    return None


def find_similar_command(word: str, mode: Optional[str] = None, min_similarity: float = 0.6) -> Optional[Tuple[str, float]]:
    """
    Find the most similar valid Cisco IOS command using fuzzy matching.

    Args:
        word: The potentially misspelled word
        mode: Optional mode to filter commands (e.g., "line_config", "global_config")
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        Tuple of (matched_command, similarity_score) if found, None otherwise

    Example:
        >>> find_similar_command("hostnane", mode="global_config")
        ('hostname', 0.875)
        >>> find_similar_command("loggin", mode="line_config")
        ('login', 0.857)
    """
    # Load vocabulary
    vocab_path = Path(__file__).parent / "cisco_commands.json"

    try:
        with open(vocab_path, 'r') as f:
            data = json.load(f)
    except Exception:
        # Fallback to cached vocabulary if file load fails
        vocab = load_command_vocabulary()
        matches = difflib.get_close_matches(word.lower(), vocab, n=1, cutoff=min_similarity)
        if matches:
            similarity = difflib.SequenceMatcher(None, word.lower(), matches[0]).ratio()
            return (matches[0], similarity)
        return None

    # Build vocabulary based on mode
    mode_commands = []

    if mode and mode in data.get("commands", {}):
        # Use mode-specific commands
        mode_commands.extend(data["commands"][mode])
        # Always include common keywords
        mode_commands.extend(data["commands"].get("common_keywords", []))
    else:
        # No mode specified or mode not found, use all commands
        for mode_cmds in data.get("commands", {}).values():
            mode_commands.extend(mode_cmds)

    # Remove duplicates and normalize
    vocab = sorted(set(cmd.lower() for cmd in mode_commands))

    # Use difflib to find close matches
    matches = difflib.get_close_matches(word.lower(), vocab, n=1, cutoff=min_similarity)

    if matches:
        # Calculate similarity score using SequenceMatcher
        similarity = difflib.SequenceMatcher(None, word.lower(), matches[0]).ratio()
        return (matches[0], similarity)

    return None


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


class FuzzyErrorPattern(RegexErrorPattern):
    """
    Enhanced error pattern with fuzzy matching for typo detection.

    This pattern extends RegexErrorPattern to identify specific typos
    by extracting the word at the ^ marker position and fuzzy matching
    it against known valid Cisco IOS commands.

    Used primarily for catch-all patterns to provide specific typo feedback.
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
        enable_fuzzy_matching: bool = True,
        fuzzy_similarity_threshold: float = 0.6,
        diagnosis_variables: Optional[List[str]] = None,
        fix_examples: Optional[List[str]] = None,
        marker_check: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a fuzzy matching error pattern.

        Args:
            pattern_id: Unique pattern identifier
            description: Human-readable description
            priority: Detection priority (higher = checked first)
            signatures: List of strings that must appear in output
            command_pattern: Dict with 'regex' and optional 'flags'
            error_type: Error type identifier
            diagnosis_template: Template string for diagnosis message
            fix_template: Template string for fix message
            enable_fuzzy_matching: Enable fuzzy matching for typos (default: True)
            fuzzy_similarity_threshold: Minimum similarity for fuzzy match (0.0-1.0, default: 0.6)
            diagnosis_variables: Variables to extract from regex matches
            fix_examples: Example fix commands
            marker_check: Optional dict with marker validation rules
            metadata: Additional metadata
        """
        super().__init__(
            pattern_id=pattern_id,
            description=description,
            priority=priority,
            signatures=signatures,
            command_pattern=command_pattern,
            error_type=error_type,
            diagnosis_template=diagnosis_template,
            fix_template=fix_template,
            diagnosis_variables=diagnosis_variables,
            fix_examples=fix_examples,
            marker_check=marker_check,
            metadata=metadata
        )

        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.fuzzy_similarity_threshold = fuzzy_similarity_threshold

    def detect(self, command: str, output: str) -> DetectionResult:
        """
        Detect error with fuzzy matching for specific typo identification.

        First runs the standard regex-based detection, then enhances
        the result with fuzzy matching if a typo is detected.
        """
        # Run standard detection
        result = super().detect(command, output)

        # If no match or fuzzy matching disabled, return as-is
        if not result.matched or not self.enable_fuzzy_matching:
            return result

        # Try to identify specific typo using marker position
        typo_info = self._identify_typo(command, output)

        if typo_info:
            # Enhance diagnosis with specific typo information
            typo_word, suggested_word, similarity = typo_info

            # Update diagnosis to be more specific
            result.diagnosis = (
                f"You have a typo in the `{typo_word}` keyword. "
                f"Did you mean `{suggested_word}`? "
                f"(similarity: {similarity:.0%})\n\n"
                f"Original diagnosis: {result.diagnosis}"
            )

            # Update fix to include the corrected command
            corrected_command = command.replace(typo_word, suggested_word, 1)
            result.fix = (
                f"Correct the typo and try again:\n"
                f"  {corrected_command}\n\n"
                f"Original suggestion: {result.fix}"
            )

            # Add typo metadata
            result.metadata["typo_detected"] = True
            result.metadata["typo_word"] = typo_word
            result.metadata["suggested_word"] = suggested_word
            result.metadata["similarity_score"] = similarity
            result.metadata["corrected_command"] = corrected_command

        return result

    def _identify_typo(self, command: str, output: str) -> Optional[Tuple[str, str, float]]:
        """
        Identify specific typo using marker position and mode-aware fuzzy matching.

        Args:
            command: The CLI command that was executed
            output: The router's error output

        Returns:
            Tuple of (typo_word, suggested_word, similarity) if found, None otherwise
        """
        # Extract the word at the marker position
        word_info = extract_word_at_marker(command, output)
        if not word_info:
            return None

        typo_word, word_index = word_info

        # Detect current Cisco mode from output
        mode = detect_cisco_mode(output)

        # Find similar valid command (mode-aware)
        match_info = find_similar_command(
            word=typo_word,
            mode=mode,
            min_similarity=self.fuzzy_similarity_threshold
        )
        if not match_info:
            return None

        suggested_word, similarity = match_info

        # Only return if the words are actually different
        if typo_word.lower() != suggested_word.lower():
            return (typo_word, suggested_word, similarity)

        return None
