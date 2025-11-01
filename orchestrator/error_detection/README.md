# Error Detection Framework

Modular, pattern-based error detection system for Cisco IOS CLI commands. Provides deterministic error identification and diagnosis for the AI tutoring system.

## Architecture

The framework consists of four main components:

### 1. Base Classes (`base.py`)

- **`ErrorPattern`**: Abstract base class for all error patterns
- **`RegexErrorPattern`**: Regex-based pattern implementation (most common)
- **`DetectionResult`**: Structured result containing error info

### 2. Pattern Registry (`registry.py`)

- **`PatternRegistry`**: Manages loading and retrieval of patterns
- **`load_default_patterns()`**: Loads patterns from JSON files
- Supports validation and error reporting

### 3. Detector Orchestrator (`detector.py`)

- **`ErrorDetector`**: Main detection coordinator
- Checks patterns in priority order
- Returns first match found
- Supports batch detection

### 4. Test Utilities (`tests.py`)

- **`PatternTester`**: Validate patterns against test cases
- **`validate_json_patterns()`**: JSON schema validation

## Usage

### Basic Usage

```python
from orchestrator.error_detection import get_default_detector

# Get the singleton detector instance
detector = get_default_detector()

# Detect errors in a CLI command
command = "hostname Router123"
output = """Floor14#hostname Router123
        ^
% Invalid input detected at '^' marker.
Floor14#"""

result = detector.detect(command, output)

if result:
    print(f"Error Type: {result.error_type}")
    print(f"Diagnosis: {result.diagnosis}")
    print(f"Fix: {result.fix}")
```

### Integration in API

```python
from orchestrator.error_detection import get_default_detector, detection_result_to_dict

def detect_cli_error(command: str, output: str) -> Optional[Dict]:
    detector = get_default_detector()
    result = detector.detect(command, output)
    return detection_result_to_dict(result)
```

## Pattern Definition Format

Patterns are defined in JSON files following this schema:

```json
{
  "version": "1.0",
  "generated_at": "2025-10-31T00:00:00Z",
  "patterns": [
    {
      "pattern_id": "unique_pattern_identifier",
      "description": "Human-readable description",
      "priority": 10,
      "signatures": [
        "String that must appear in output",
        "Another signature string"
      ],
      "command_pattern": {
        "regex": "python_regex_pattern",
        "flags": "IGNORECASE"
      },
      "marker_check": {
        "enabled": true,
        "description": "Optional ^ marker validation",
        "expected_position": "before_slash|at_char|end_of_command"
      },
      "error_type": "ERROR_TYPE_NAME",
      "diagnosis": {
        "template": "The command '{command}' [explanation]",
        "variables": ["command", "address", "prefix"]
      },
      "fix": {
        "template": "[Action]: [correct syntax]",
        "examples": ["correct command example"]
      },
      "metadata": {
        "affected_modes": ["privileged_exec", "global_config"],
        "cisco_ios_versions": ["12.x", "15.x", "IOS-XE"],
        "common_student_mistake": true
      }
    }
  ]
}
```

## Pattern Files

### `patterns/hardcoded.json`

Manually defined patterns for well-understood error cases. Currently includes:
- **wrong_mode_config_commands**: Config commands in privileged exec mode
- **wrong_mode_interface_commands**: Interface commands outside interface config mode

### `patterns/generated/patterns.json`

LLM-generated patterns extracted from real router error sessions using frontier models (GPT-5, Claude Sonnet 4.5).

**To generate new patterns:**
1. Capture error session on real router
2. Use the prompt from `docs/error-pattern-generation-prompt.md`
3. Feed to frontier LLM (ChatGPT o1 or Claude Sonnet 4.5)
4. Add generated patterns to this file

## Priority System

Patterns are checked in priority order (highest first):

- **10**: Mode errors (very common, cheap to check)
- **8**: Specific syntax errors (IPv6, CIDR)
- **5**: General syntax errors
- **3**: Typos and incomplete commands
- **1**: Fallback patterns

## Error Types

Error types use `SCREAMING_SNAKE_CASE` naming:

- `WRONG_MODE` - Command in incorrect mode
- `IPV6_PREFIX_SYNTAX` - IPv6 prefix length syntax error
- `CIDR_NOT_SUPPORTED` - CIDR notation instead of subnet mask
- `INCOMPLETE_COMMAND` - Missing required parameters
- `TYPO_IN_COMMAND` - Misspelled command
- `INVALID_IP_FORMAT` - Malformed IP address

## Testing

Run the framework test suite:

```bash
python test_framework.py
```

Test specific patterns:

```python
from orchestrator.error_detection import get_default_detector
from orchestrator.error_detection.tests import PatternTester

detector = get_default_detector()
tester = PatternTester(detector)

test_cases = [
    {
        "command": "hostname Router1",
        "output": "Floor14#hostname Router1\n        ^\n% Invalid input...",
        "should_match": True,
        "expected_type": "WRONG_MODE"
    }
]

passed, failed, failures = tester.test_pattern("wrong_mode_config_commands", test_cases)
tester.print_test_results("WRONG_MODE Test", passed, failed, failures)
```

## Extending the Framework

### Adding New Patterns

1. **Create JSON definition** in `patterns/generated/patterns.json` or `patterns/hardcoded.json`
2. **Validate** using `validate_json_patterns()`
3. **Test** with real examples
4. **Reload** detector if running: `reload_default_detector()`

### Creating Custom Pattern Classes

For complex detection logic that doesn't fit the regex model:

```python
from orchestrator.error_detection.base import ErrorPattern, DetectionResult

class CustomPattern(ErrorPattern):
    def __init__(self):
        super().__init__(
            pattern_id="custom_pattern",
            description="Custom detection logic",
            priority=5,
            error_type="CUSTOM_ERROR"
        )

    def detect(self, command: str, output: str) -> DetectionResult:
        # Custom detection logic
        if some_complex_condition(command, output):
            return DetectionResult(
                matched=True,
                error_type=self.error_type,
                command=command,
                diagnosis="Custom diagnosis",
                fix="Custom fix"
            )
        return DetectionResult(matched=False)

# Register with detector
from orchestrator.error_detection import get_default_detector
detector = get_default_detector()
detector.registry.register(CustomPattern())
```

## Performance

- **Pattern loading**: Lazy initialization on first use
- **Detection**: O(n) where n = number of patterns (short-circuits on first match)
- **Regex compilation**: Patterns compiled once at load time
- **Memory**: ~1KB per pattern definition

## Future Enhancements

1. **Context-aware detection**: Pass current mode, device type, etc.
2. **Multi-pattern matching**: Return multiple applicable patterns
3. **Pattern statistics**: Track which patterns match most frequently
4. **Hot reload**: Reload patterns without restarting server
5. **Pattern grouping**: Organize related patterns into families

## File Structure

```
orchestrator/error_detection/
├── __init__.py              # Public API
├── base.py                  # Base classes
├── detector.py              # Main orchestrator
├── registry.py              # Pattern loading/management
├── tests.py                 # Testing utilities
├── README.md                # This file
└── patterns/
    ├── __init__.py
    ├── hardcoded.json       # Manual patterns
    └── generated/
        ├── __init__.py
        └── patterns.json    # LLM-generated patterns
```

## Integration Points

### API Layer (`api/main.py`)

- `detect_cli_error()` function uses framework
- `/api/cli/analyze` endpoint caches diagnoses

### Orchestrator Layer (`orchestrator/nodes.py`)

- `feedback_node_stream()` injects cached diagnoses into prompts

### Frontend (`frontend/src/features/simulator/Terminal.tsx`)

- Automatically analyzes commands after execution
- Non-blocking, fire-and-forget analysis

## Contributing

When adding new patterns:

1. Use the LLM-assisted generation workflow (see `docs/error-pattern-generation-prompt.md`)
2. Test against real router output
3. Ensure no overlaps with existing patterns
4. Document in pattern's `description` field
5. Add test cases to verify correctness
