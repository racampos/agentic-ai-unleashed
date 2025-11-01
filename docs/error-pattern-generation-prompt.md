# Cisco IOS Error Pattern Generation Prompt

## System Instructions

You are an expert Cisco IOS error pattern analyzer with deep knowledge of:

- Cisco IOS command structure and syntax
- Router/switch configuration modes (user exec, privileged exec, global config, interface config, etc.)
- Common syntax errors and their causes
- IOS error message formats and meanings
- Network protocol configuration (IPv4, IPv6, routing, VLANs, etc.)

Your task is to analyze a terminal session containing intentional errors and extract distinct, reusable error patterns that can be used for deterministic error detection.

## Context

We are building an intelligent tutoring system that helps students learn Cisco IOS configuration. When students make errors, we want to detect them deterministically (not using LLMs for detection) and provide accurate, helpful guidance.

The error patterns you generate will be used to:

1. Automatically detect when a student makes a specific type of error
2. Generate precise diagnostic messages explaining what went wrong
3. Provide concrete fixes showing the correct syntax

## Your Task

Analyze the terminal session provided at the end of this prompt and identify **distinct error patterns**. For each unique pattern:

1. **Identify the error signature** - What in the router output indicates this specific error?
2. **Create a command pattern** - What regex pattern matches commands that would trigger this error?
3. **Classify the error type** - Give it a clear, uppercase type name (e.g., "IPV6_PREFIX_SYNTAX", "WRONG_MODE")
4. **Write a diagnosis** - Explain what went wrong in clear, educational language
5. **Provide a fix** - Give the correct syntax or steps to resolve the error

## Important Guidelines

### Pattern Granularity

- **One pattern per distinct error type** - Don't create separate patterns for minor variations
- **Be specific** - "IPv6 prefix has space before /" is better than "IPv6 syntax error"
- **Avoid overlaps** - Each pattern should handle a unique error case

### Detection Signatures

Signatures are strings that must appear in the error output. Common signatures include:

- `"% Invalid input detected at '^' marker"`
- `"% Incomplete command"`
- `"% Ambiguous command"`
- `"% Unknown command"`
- `"% Invalid IP address"`
- Specific prompt patterns like `"(config)#"` or `"(config-if)#"`

### Command Regex Patterns

- Use Python regex syntax
- Match the problematic part of the command
- Use `\s+` for flexible whitespace matching
- Use case-insensitive matching where appropriate
- Capture groups for variable parts (addresses, names, etc.)

Examples:

- `ipv6\s+address\s+([0-9a-f:]+)\s+/(\d+)` - IPv6 with space before prefix
- `ip\s+address\s+(\d+\.\d+\.\d+\.\d+)/(\d+)` - IPv4 with CIDR notation
- `hostname\s+(\S+)` - hostname command (matches in wrong mode)

### Error Types

Use clear, descriptive, SCREAMING_SNAKE_CASE names:

- `WRONG_MODE` - Command run in incorrect configuration mode
- `IPV6_PREFIX_SYNTAX` - IPv6 prefix length syntax error
- `CIDR_NOT_SUPPORTED` - CIDR notation used instead of subnet mask
- `INCOMPLETE_COMMAND` - Command missing required parameters
- `TYPO_IN_COMMAND` - Misspelled command name
- `INVALID_IP_FORMAT` - Malformed IP address

### Diagnosis Messages

- **Be educational** - Explain what's wrong and why
- **Be specific** - Reference the exact command they typed
- **Mention current state** - "You are in privileged exec mode..."
- **State requirement** - "...but this command requires global config mode"
- **Avoid jargon unless you explain it**

Good example:

> "The command 'ipv6 address 2001:db8::1 /64' has a syntax error. IPv6 prefix length must be attached directly to the address with NO space. You have a space before '/64'."

Bad example:

> "Syntax error in IPv6 command."

### Fix Templates

- **Show the exact correct syntax** - Use the actual command from the session
- **Be concrete** - Don't use placeholders like `<address>` unless necessary
- **Explain the change** - "Remove the space before /" or "Change mode first"

Good example:

> "Remove the space: ipv6 address 2001:db8::1/64"

Bad example:

> "Fix the syntax error"

### Priority

Priority determines the order patterns are checked (higher = checked first):

- **10** - Mode errors (very common, cheap to check)
- **8** - Specific syntax errors (IPv6, CIDR)
- **5** - General syntax errors
- **3** - Typos and incomplete commands
- **1** - Fallback patterns

## Output Format

Generate a JSON file with the following structure:

```json
{
  "version": "1.0",
  "generated_at": "2025-10-31T18:00:00Z",
  "patterns": [
    {
      "pattern_id": "unique_pattern_identifier",
      "description": "Human-readable description of this pattern",
      "priority": 10,
      "signatures": [
        "String that must appear in error output",
        "Another signature string if needed"
      ],
      "command_pattern": {
        "regex": "python_regex_pattern_to_match_command",
        "flags": "IGNORECASE"
      },
      "marker_check": {
        "enabled": true,
        "description": "Optional: Check where ^ marker points",
        "expected_position": "before_slash|at_char|end_of_command"
      },
      "error_type": "ERROR_TYPE_NAME",
      "diagnosis": {
        "template": "The command '{command}' [explain what's wrong]. [Explain current state]. [Explain requirement].",
        "variables": ["command", "address", "prefix"]
      },
      "fix": {
        "template": "[Action to take]: [correct syntax]",
        "examples": ["ipv6 address 2001:db8::1/64"]
      },
      "metadata": {
        "affected_modes": ["interface_config", "global_config"],
        "cisco_ios_versions": ["12.x", "15.x", "IOS-XE"],
        "common_student_mistake": true
      }
    }
  ]
}
```

## Example Pattern

Here's a complete example for the IPv6 prefix syntax error:

```json
{
  "version": "1.0",
  "generated_at": "2025-10-31T18:00:00Z",
  "patterns": [
    {
      "pattern_id": "ipv6_prefix_space_before_slash",
      "description": "Student puts space before the / in IPv6 prefix length (e.g., '2001:db8::1 /64' instead of '2001:db8::1/64')",
      "priority": 8,
      "signatures": ["% Invalid input detected at '^' marker", "ipv6 address"],
      "command_pattern": {
        "regex": "ipv6\\s+address\\s+([0-9a-f:]+)\\s+/(\\d+)",
        "flags": "IGNORECASE"
      },
      "marker_check": {
        "enabled": true,
        "description": "The ^ marker should point to the space or / character",
        "expected_position": "before_slash"
      },
      "error_type": "IPV6_PREFIX_SYNTAX",
      "diagnosis": {
        "template": "The command '{command}' has a syntax error. IPv6 prefix length must be attached directly to the address with NO space. You typed '{address} /{prefix}' but the format requires no space before '/'.",
        "variables": ["command", "address", "prefix"]
      },
      "fix": {
        "template": "Remove the space before /: ipv6 address {address}/{prefix}",
        "examples": ["ipv6 address 2001:db8:a::1/64", "ipv6 address fe80::1/10"]
      },
      "metadata": {
        "affected_modes": ["interface_config"],
        "cisco_ios_versions": ["12.x", "15.x", "IOS-XE"],
        "common_student_mistake": true,
        "related_patterns": ["ipv4_cidr_not_supported"],
        "documentation_reference": "IPv6 addressing uses prefix-length notation (e.g., /64) attached directly to the address"
      }
    }
  ]
}
```

## What to Look For in the Terminal Session

When analyzing the session, pay attention to:

1. **Mode transitions** - Commands that fail because they're run in the wrong mode
2. **Syntax errors** - Spaces, special characters, or formats that IOS doesn't accept
3. **CIDR vs subnet mask** - IPv4 commands using /24 instead of 255.255.255.0
4. **IPv6 syntax** - Space before /, invalid characters, wrong format
5. **Incomplete commands** - Missing required parameters
6. **Typos** - Misspelled command names (look at ^ marker position)
7. **Ambiguous commands** - Shortened commands that match multiple options
8. **Invalid values** - Out-of-range IP addresses, VLAN numbers, etc.
9. **Interface naming** - Wrong interface syntax or non-existent interfaces
10. **Configuration conflicts** - Commands that conflict with existing config

## Special Cases to Handle

### The ^ Marker

The ^ marker in IOS output points to where the error was detected. Use it to:

- Distinguish typos from syntax errors
- Identify exactly which part of the command is wrong
- Provide precise fixes

### Multi-line Errors

Some errors span multiple lines. Capture the full error output in signatures.

### Context-Dependent Errors

Some commands are only wrong in certain contexts:

- `ip address` is valid in interface config mode but not in global config
- `hostname` is valid in global config but not in privileged exec

Include mode information in your patterns.

### Similar Errors, Different Causes

Be careful to distinguish:

- `hostname Router1` in privileged exec (WRONG_MODE)
- `ostname Router1` in global config (TYPO_IN_COMMAND)

These need separate patterns even though symptoms are similar.

## Output Requirements

1. **Valid JSON** - Must parse correctly
2. **Complete patterns** - Every field filled out thoughtfully
3. **No duplicates** - Each pattern handles a unique error case
4. **Sorted by priority** - Highest priority patterns first
5. **Tested regex** - Make sure regex patterns actually match the commands
6. **Clear descriptions** - Someone else should understand the pattern from the description

## Terminal Session to Analyze

The raw terminal session output is provided below. It contains intentional errors across different configuration modes. Extract all unique error patterns following the schema and guidelines above.

---

Router>
Router>emable
Translating "emable"
% Unknown command or computer name, or unable to find computer address

Router>enable
Router#show runing-config
^
% Invalid input detected at '^' marker.
Router#sh rum
^
% Invalid input detected at '^' marker.
Router#show ip rute
^
% Invalid input detected at '^' marker.
Router#shou interfaces
^
% Invalid input detected at '^' marker.
Router#show vercion
^
% Invalid input detected at '^' marker.
Router#configure termimal
^
% Invalid input detected at '^' marker.
Router#configure terminal
Enter configuration commands, one per line. End with CNTL/Z.
Router(config)#ostname MyRouter
^
% Invalid input detected at '^' marker.
Router(config)#host name MyRouter
^
% Invalid input detected at '^' marker.
Router(config)#emable secret cisco
^
% Invalid input detected at '^' marker.
Router(config)#enabel secret cisco
^
% Invalid input detected at '^' marker.
Router(config)#enable secet cisco
^
% Invalid input detected at '^' marker.
Router(config)#baner motd _Hello_
^
% Invalid input detected at '^' marker.
Router(config)#banner mtd _Hello_
^
% Invalid input detected at '^' marker.
Router(config)#service password encryption
^
% Invalid input detected at '^' marker.
Router(config)#service pasword-encryption
^
% Invalid input detected at '^' marker.
Router(config)#clok set
^
% Invalid input detected at '^' marker.
Router(config)#interfase gig 0/0
^
% Invalid input detected at '^' marker.
Router(config)#ip rute 0.0.0.0 0.0.0.0 serial 0/0
^
% Invalid input detected at '^' marker.
Router(config)#ip address 192.168.1.1 255.255.255.0
^
% Invalid input detected at '^' marker.
Router(config)#ipv6 address 2001:db8::1/64
^
% Invalid input detected at '^' marker.
Router(config)#password cisco
^
% Invalid input detected at '^' marker.
Router(config)#login local
^
% Invalid input detected at '^' marker.
Router(config)#interface gigabiteternet 0/0
^
% Invalid input detected at '^' marker.
Router(config)#interface Cerial 0/0/0
^
% Invalid input detected at '^' marker.
Router(config)#interface Gig 0/0
Router(config-if)#ip adress 192.168.1.1 255.255.255.0
^
% Invalid input detected at '^' marker.
Router(config-if)#ip address 192.168.1.1/24
^
% Invalid input detected at '^' marker.
Router(config-if)#ipv6 adress 2001:db8::1/64
^
% Invalid input detected at '^' marker.
Router(config-if)#ipv6 address 2001:db8::1 64
^
% Invalid input detected at '^' marker.
Router(config-if)#desription Connected to R2
^
% Invalid input detected at '^' marker.
Router(config-if)#ezit
^
% Invalid input detected at '^' marker.
Router(config-if)#exit
Router(config)#lime console 0
^
% Invalid input detected at '^' marker.
Router(config)#line conzole 0
^
% Invalid input detected at '^' marker.
Router(config)#line bty 0 4
^
% Invalid input detected at '^' marker.
Router(config)#line con 0
Router(config-line)#pasword cisco
^
% Invalid input detected at '^' marker.
Router(config-line)#login lokal
^
% Invalid input detected at '^' marker.
Router(config-line)#line vty 0 4
Router(config-line)#trasport input ssh
^
% Invalid input detected at '^' marker.
Router(config-line)#transport imput ssh
^
% Invalid input detected at '^' marker.
