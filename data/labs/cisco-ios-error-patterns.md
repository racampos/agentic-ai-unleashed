# Cisco IOS Error Pattern Diagnosis Guide

## How to Use This Guide

When a student encounters an error, follow these diagnostic steps:

1. **Identify the error type** from the error message
2. **Locate the ^ marker position** (if present) - it points to where IOS detected the problem
3. **Compare student's command** against correct syntax
4. **Check the specific pattern** below for diagnosis

---

## Error Pattern 1: Invalid Input Detected at '^' Marker

### Error Message Format:
```
% Invalid input detected at '^' marker.
```

The caret (^) symbol points EXACTLY to where Cisco IOS detected the problem.

### Diagnostic Steps:

1. **Look at what character the ^ is pointing to**
2. **Check the patterns below** for the most common causes

---

### Pattern 1A: Space in Command Name

**Symptom:** The ^ marker points to a letter in the middle of what should be a single command word.

**Example 1:**
```
Floor14(config)#host name Router1
Floor14(config)#host name Router1
                     ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** The space between "host" and "name" is the problem. IOS sees "host" as a complete (but incorrect) command, then doesn't know what to do with "name".

**The ^ points to:** The 'n' in "name" - the first character after the space

**Correct command:** `hostname Router1` (no space in command word)

**Example 2:**
```
Floor14(config-if)#no shut down
Floor14(config-if)#no shut down
                         ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** Space between "shut" and "down"

**The ^ points to:** The 'd' in "down"

**Correct command:** `no shutdown` (no space)

**Example 3:**
```
Floor14(config-if)#ip add ress 192.168.1.1 255.255.255.0
Floor14(config-if)#ip add ress 192.168.1.1 255.255.255.0
                      ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** Space between "add" and "ress"

**Correct command:** `ip address 192.168.1.1 255.255.255.0` (no space in "address")

**Key Pattern:** If ^ points to a letter in the middle of a word that you intended as one command, there's likely an unwanted space before it.

---

### Pattern 1B: Typo in Command Name

**Symptom:** The ^ marker points near the beginning or middle of a command that looks "almost right"

**Example 1:**
```
Floor14(config)#hostnsme MyRouter
Floor14(config)#hostnsme MyRouter
                    ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** "hostnsme" is not a valid command - it's a typo for "hostname"

**The ^ points to:** Where IOS determined this is not a valid command (often near the typo)

**Correct command:** `hostname MyRouter`

**Example 2:**
```
Floor14(config-if)#ip adress 192.168.1.1 255.255.255.0
Floor14(config-if)#ip adress 192.168.1.1 255.255.255.0
                      ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** "adress" is a typo for "address" (missing one 'd')

**Correct command:** `ip address 192.168.1.1 255.255.255.0`

**Example 3:**
```
Floor14#cofigure terminal
Floor14#cofigure terminal
            ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** "cofigure" is a typo for "configure" (missing 'n')

**Correct command:** `configure terminal`

**Key Pattern:** If the command looks almost right but IOS doesn't recognize it, check spelling carefully against the reference.

**Common typos:**
- `hostnsme` → `hostname`
- `hotsname` → `hostname`
- `adress` → `address`
- `cofigure` → `configure`
- `interfce` → `interface`
- `runnig-config` → `running-config`
- `shut down` → `shutdown`

---

### Pattern 1C: Wrong Configuration Mode

**Symptom:** Valid command syntax, but ^ marker appears because you're in the wrong mode

**Example 1:**
```
Floor14#hostname Router1
Floor14#hostname Router1
            ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** You're in privileged EXEC mode (`Floor14#`) but `hostname` requires global configuration mode

**Current mode:** Privileged EXEC mode (`Router#`)

**Required mode:** Global configuration mode (`Router(config)#`)

**Fix:** Enter configuration mode first:
```
Floor14#configure terminal
Floor14(config)#hostname Router1
```

**Example 2:**
```
Floor14(config)#ip address 192.168.1.1 255.255.255.0
Floor14(config)#ip address 192.168.1.1 255.255.255.0
                   ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** You're in global configuration mode (`config)#`) but `ip address` requires interface configuration mode

**Current mode:** Global configuration mode (`Router(config)#`)

**Required mode:** Interface configuration mode (`Router(config-if)#`)

**Fix:** Enter interface mode first:
```
Floor14(config)#interface GigabitEthernet0/0
Floor14(config-if)#ip address 192.168.1.1 255.255.255.0
```

**Key Pattern:** If the command syntax looks correct but fails, check the prompt to verify you're in the right configuration mode.

**Mode Indicators:**
- `Router>` = User EXEC mode
- `Router#` = Privileged EXEC mode
- `Router(config)#` = Global configuration mode
- `Router(config-if)#` = Interface configuration mode
- `Router(config-router)#` = Router configuration mode
- `Router(config-line)#` = Line configuration mode

---

### Pattern 1D: CIDR Notation Instead of Subnet Mask

**Symptom:** ^ marker points to the `/` character in CIDR notation like `/24`

**Example:**
```
Floor14(config-if)#ip address 192.168.1.1/24
Floor14(config-if)#ip address 192.168.1.1/24
                                          ^
% Invalid input detected at '^' marker.
```

**Diagnosis:** Cisco IOS does NOT support CIDR notation (e.g., `/24`). You must use full subnet mask format.

**The ^ points to:** The `/` character

**Incorrect:** `ip address 192.168.1.1/24`

**Correct:** `ip address 192.168.1.1 255.255.255.0`

**CIDR to Subnet Mask Conversion:**
- `/8` = `255.0.0.0`
- `/16` = `255.255.0.0`
- `/24` = `255.255.255.0`
- `/25` = `255.255.255.128`
- `/26` = `255.255.255.192`
- `/27` = `255.255.255.224`
- `/28` = `255.255.255.240`
- `/29` = `255.255.255.248`
- `/30` = `255.255.255.252`

**Key Pattern:** If you see `/` in an IP address command, that's CIDR notation and Cisco IOS doesn't support it - convert to subnet mask format.

---

## Error Pattern 2: Incomplete Command

### Error Message Format:
```
% Incomplete command.
```

**Symptom:** You entered a valid command but didn't provide all required parameters.

**Example 1:**
```
Floor14(config-if)#ip address
% Incomplete command.
```

**Diagnosis:** `ip address` requires both an IP address AND subnet mask

**Correct command:** `ip address 192.168.1.1 255.255.255.0`

**Example 2:**
```
Floor14(config)#hostname
% Incomplete command.
```

**Diagnosis:** `hostname` requires a name parameter

**Correct command:** `hostname Router1`

**Example 3:**
```
Floor14(config)#interface
% Incomplete command.
```

**Diagnosis:** `interface` requires interface type and number

**Correct command:** `interface GigabitEthernet0/0`

**Key Pattern:** Press `?` after the command to see what parameters are required.

---

## Error Pattern 3: Ambiguous Command

### Error Message Format:
```
% Ambiguous command: "..."
```

**Symptom:** You abbreviated a command, but multiple commands start with those letters.

**Example 1:**
```
Floor14(config)#int
% Ambiguous command: "int"
```

**Diagnosis:** Multiple commands start with "int" (e.g., `interface`, `interface-range`)

**Fix:** Use more letters to be specific:
- `inter` for `interface`
- Or just type the full word: `interface`

**Example 2:**
```
Floor14#sh ru
% Ambiguous command: "sh ru"
```

**Diagnosis:** "ru" could be `running-config`, `running`, etc.

**Fix:** Type more letters: `sh run` or `show running-config`

**Key Pattern:** Add more letters until the command is unambiguous, or type the full command.

---

## Error Pattern 4: Unrecognized Command

### Error Message Format:
```
% Unrecognized command
```

**Symptom:** The command doesn't exist in Cisco IOS at all.

**Example 1:**
```
Floor14#ifconfig
% Unrecognized command
```

**Diagnosis:** `ifconfig` is a Linux/Unix command, not Cisco IOS. The IOS equivalent is `show ip interface brief`

**Correct command:** `show ip interface brief`

**Example 2:**
```
Floor14(config-if)#set ip 192.168.1.1
% Unrecognized command
```

**Diagnosis:** "set ip" is not valid IOS syntax

**Correct command:** `ip address 192.168.1.1 255.255.255.0`

**Key Pattern:** Check the command reference for the correct IOS syntax. Many network commands from other systems don't work in IOS.

---

## Diagnostic Decision Tree

When a student encounters an error, follow this flowchart:

1. **Is there a ^ marker?**
   - YES → Look at what character ^ points to:
     - Points to a letter mid-word? → Check for **space in command name** (Pattern 1A)
     - Points near start of word? → Check for **typo** (Pattern 1B)
     - Points to `/` ? → Check for **CIDR notation** (Pattern 1D)
     - Command looks correct? → Check **configuration mode** (Pattern 1C)
   - NO → Continue to step 2

2. **Does error say "Incomplete command"?**
   - YES → **Missing required parameters** (Pattern 2)
   - NO → Continue to step 3

3. **Does error say "Ambiguous command"?**
   - YES → **Need more specific abbreviation** (Pattern 3)
   - NO → Continue to step 4

4. **Does error say "Unrecognized command"?**
   - YES → **Wrong command or wrong IOS syntax** (Pattern 4)
   - NO → Check other error types

---

## Tutoring Guidelines for Error Analysis

When helping a student with an error:

1. **Quote the exact error** from their terminal output
2. **Point out the ^ marker position** if present - it's the key diagnostic clue
3. **Explain what the error means** in their specific context
4. **Show the correct syntax** with their parameters
5. **Explain why** the error occurred (learning opportunity)

**Example Good Response:**

> I can see from your terminal that you typed:
> ```
> Floor14(config)#host name Router1
>                      ^
> % Invalid input detected at '^' marker.
> ```
>
> The `^` marker is pointing to the 'n' in "name". This tells us that Cisco IOS saw "host" as a complete command (which doesn't exist), and then didn't know what to do with "name".
>
> The issue is that **"hostname" must be typed as one word with no space**.
>
> **Correct command:**
> ```
> Floor14(config)#hostname Router1
> ```
>
> This is a common mistake - many Cisco IOS commands that seem like they should be two words are actually one word: `hostname`, `shutdown`, `running-config`, etc.

**Example Bad Response:**

> You need to use the hostname command in global configuration mode. The syntax is `hostname [name]`. Make sure you're in the right mode.

(This doesn't address the actual error - the space in "host name")

---

## Priority Error Patterns for RAG Retrieval

When CLI errors are detected, these patterns should be prioritized in semantic search:

1. **CIDR notation errors** (highest priority - very specific pattern)
2. **Space in command name** (high priority - extremely common)
3. **Typos** (high priority - common but harder to detect)
4. **Wrong mode** (medium priority - context dependent)
5. **Incomplete command** (medium priority - usually obvious)
6. **Ambiguous command** (low priority - error message is clear)

---

## Common Command Corrections Quick Reference

| Student Types | Error | Correct Command |
|--------------|-------|-----------------|
| `host name Router1` | Invalid input at ^ | `hostname Router1` |
| `hostnsme Router1` | Invalid input at ^ | `hostname Router1` |
| `shut down` | Invalid input at ^ | `shutdown` |
| `no shut down` | Invalid input at ^ | `no shutdown` |
| `ip add ress` | Invalid input at ^ | `ip address` |
| `ip adress` | Invalid input at ^ | `ip address` |
| `ip address 192.168.1.1/24` | Invalid input at ^ | `ip address 192.168.1.1 255.255.255.0` |
| `cofigure terminal` | Invalid input at ^ | `configure terminal` |
| `conf t` | ✓ Valid | `configure terminal` |
| `show run` | ✓ Valid | `show running-config` |
| `show running interface` | Invalid | `show running-config interface [name]` |
| `ifconfig` | Unrecognized | `show ip interface brief` |
| `sh ip int br` | ✓ Valid | `show ip interface brief` |

---

## Summary: Key Diagnostic Rules

1. **The ^ marker is your best friend** - it points EXACTLY to where IOS detected the problem
2. **Check for spaces in single-word commands** - extremely common error
3. **Check spelling against command reference** - typos are common
4. **Check the prompt** - are you in the right mode?
5. **CIDR notation doesn't work** - always use subnet mask format
6. **Press ? for help** - IOS has built-in help at every step

When in doubt, have the student:
1. Type the command up to where they're stuck
2. Press `?` to see valid options
3. This shows them exactly what IOS expects next
