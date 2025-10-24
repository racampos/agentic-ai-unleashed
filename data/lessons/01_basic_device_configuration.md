# Basic Device Configuration

## Introduction

This lesson covers fundamental Cisco device configuration concepts including hostname setup, interface configuration, and basic network connectivity. You'll learn how to configure routers and switches in a simple network topology.

## Learning Objectives

By the end of this lesson, you will be able to:
- Configure device hostnames
- Set up basic interface configurations
- Understand VLAN concepts
- Verify device connectivity
- Use basic show commands

## Topology Overview

The lab environment consists of:
- **1 Router** (Floor14): Central routing device connecting two switch networks
- **2 Switches** (Room-145, Room-146): Access layer switches for end devices
- **4 Hosts**: Manager and Reception workstations in two separate rooms

### Network Design

```
Floor14 (Router)
├── Gi0/0 → Room-145 (Switch)
│   ├── Fa0/1 → Manager-A
│   └── Fa0/2 → Reception-A
└── Gi0/1 → Room-146 (Switch)
    ├── Fa0/1 → Manager-B
    └── Fa0/2 → Reception-B
```

## Device Hostname Configuration

### Setting the Hostname

The hostname is the device's name displayed in the CLI prompt. It helps identify devices in the network.

**Command:**
```
Router> enable
Router# configure terminal
Router(config)# hostname Floor14
Floor14(config)#
```

**Best Practices:**
- Use descriptive names (location, function, or purpose)
- Avoid spaces (use hyphens or underscores)
- Keep names under 64 characters
- Use consistent naming conventions

### Verification

To verify your hostname configuration:
```
Floor14# show running-config | include hostname
hostname Floor14
```

## Interface Configuration

### Understanding Interface Names

Cisco devices use hierarchical interface naming:
- **GigabitEthernet0/0**: First Gigabit interface on router
- **FastEthernet0/1**: Second FastEthernet port on switch
- Format: `Type slot/port` or `Type module/slot/port`

### Basic Interface Commands

**Bringing an Interface Up:**
```
Floor14(config)# interface GigabitEthernet0/0
Floor14(config-if)# no shutdown
Floor14(config-if)# description Connection to Room-145
```

**Viewing Interface Status:**
```
Floor14# show ip interface brief
```

Expected output shows:
- Interface name
- IP address (if configured)
- Status (up/down/administratively down)
- Protocol status

## Common Commands Reference

### Show Commands

| Command | Purpose |
|---------|---------|
| `show running-config` | Display current configuration |
| `show ip interface brief` | Quick interface status overview |
| `show interfaces` | Detailed interface information |
| `show version` | Device hardware and IOS version |
| `show ip route` | Display routing table |

### Configuration Mode Navigation

| Command | Action |
|---------|--------|
| `enable` | Enter privileged EXEC mode |
| `configure terminal` | Enter global configuration mode |
| `interface [name]` | Enter interface configuration mode |
| `exit` | Move up one configuration level |
| `end` | Return to privileged EXEC mode |

## Troubleshooting Tips

### Interface is Down

**Problem**: Interface shows "administratively down"

**Solution**: Use `no shutdown` command
```
Floor14(config)# interface GigabitEthernet0/0
Floor14(config-if)# no shutdown
```

### Cannot Ping Between Devices

**Checklist**:
1. Verify both interfaces are up: `show ip interface brief`
2. Check IP addresses are in the same subnet
3. Verify no access-lists blocking traffic
4. Ensure cables are properly connected

### Configuration Not Saving

**Problem**: Changes lost after reload

**Solution**: Save configuration to startup-config
```
Floor14# copy running-config startup-config
```

Or use the shortcut:
```
Floor14# write memory
```

## Practice Exercise

### Task 1: Configure Device Hostnames

1. Connect to each device in the topology
2. Set hostnames according to the topology diagram
3. Verify with `show running-config | include hostname`

### Task 2: Interface Status Check

1. Check interface status on Floor14 router
2. Identify which interfaces are up/down
3. Bring up any administratively down interfaces

### Task 3: Connectivity Verification

1. Verify connectivity between Floor14 and both switches
2. Document which show command you used
3. Save your configuration

## Key Takeaways

- **Hostnames** make device identification easier
- **no shutdown** is required to activate interfaces
- **show commands** are essential for verification
- Always **save your configuration** with `copy run start`
- Interface status shows both **physical (status)** and **data link (protocol)** layers

## Next Steps

Once you've mastered basic device configuration, you're ready to move on to:
- IP Address configuration
- VLAN configuration
- Basic routing concepts
- Access control lists (ACLs)
