---
id: 01-basic-routing
title: Basic Router Configuration
description: Configure basic router settings including hostname, passwords, and IP addresses on router interfaces.
difficulty: beginner
estimated_time: 30
topology_file: 01-basic-routing.yaml
diagram_file: 01_basic_routing.png
prerequisites: []
---

# Lab 1: Basic Router Configuration

## Lab Objectives
- Configure basic router settings (hostname, passwords)
- Configure IP addresses on router interfaces
- Verify interface status and IP configuration
- Test connectivity using ping

## Lab Topology
- Router R1 with two interfaces:
  - GigabitEthernet0/0: 192.168.1.1/24
  - GigabitEthernet0/1: 192.168.2.1/24

## Prerequisites
- Understanding of IP addressing and subnetting
- Basic CLI navigation skills
- Familiarity with Cisco IOS command structure

## Step 1: Access the Router and Enter Privileged Mode

To begin configuration, you need to access the router's command-line interface (CLI) and enter privileged EXEC mode.

**Commands:**
```
Router> enable
Router#
```

**Explanation:**
- The `enable` command transitions from user EXEC mode (>) to privileged EXEC mode (#)
- Privileged EXEC mode allows you to view all router configurations and make changes

**Expected Output:**
```
Router> enable
Router#
```

## Step 2: Enter Global Configuration Mode

Global configuration mode allows you to make changes that affect the entire router.

**Commands:**
```
Router# configure terminal
Router(config)#
```

**Explanation:**
- `configure terminal` (or `conf t` for short) enters global configuration mode
- The prompt changes to (config)# indicating you're in global configuration mode

## Step 3: Configure Router Hostname

Setting a descriptive hostname helps identify the router in a network.

**Commands:**
```
Router(config)# hostname R1
R1(config)#
```

**Explanation:**
- `hostname R1` sets the router's name to "R1"
- Notice the prompt immediately changes to reflect the new hostname

## Step 4: Configure Console Password

Securing console access is a basic security measure.

**Commands:**
```
R1(config)# line console 0
R1(config-line)# password cisco
R1(config-line)# login
R1(config-line)# exit
R1(config)#
```

**Explanation:**
- `line console 0` enters console line configuration mode
- `password cisco` sets the console password to "cisco"
- `login` enables password checking on the console line
- `exit` returns to global configuration mode

## Step 5: Configure Enable Password

The enable password protects privileged EXEC mode.

**Commands:**
```
R1(config)# enable secret class
R1(config)#
```

**Explanation:**
- `enable secret class` sets an encrypted password for privileged EXEC mode
- Use `enable secret` (encrypted) instead of `enable password` (plain text)
- The password "class" will be required when using the `enable` command

## Step 6: Configure Interface GigabitEthernet0/0

Now we'll configure the first interface with an IP address.

**Commands:**
```
R1(config)# interface gigabitethernet 0/0
R1(config-if)# ip address 192.168.1.1 255.255.255.0
R1(config-if)# description LAN 1
R1(config-if)# no shutdown
R1(config-if)# exit
R1(config)#
```

**Explanation:**
- `interface gigabitethernet 0/0` (or `int g0/0`) enters interface configuration mode
- `ip address 192.168.1.1 255.255.255.0` assigns the IP and subnet mask
- `description LAN 1` adds a description for documentation
- `no shutdown` activates the interface (interfaces are shutdown by default)

**Expected Output:**
```
%LINK-5-CHANGED: Interface GigabitEthernet0/0, changed state to up
%LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/0, changed state to up
```

## Step 7: Configure Interface GigabitEthernet0/1

Repeat the process for the second interface.

**Commands:**
```
R1(config)# interface gigabitethernet 0/1
R1(config-if)# ip address 192.168.2.1 255.255.255.0
R1(config-if)# description LAN 2
R1(config-if)# no shutdown
R1(config-if)# exit
R1(config)#
```

## Step 8: Save the Configuration

Always save your configuration to ensure changes persist after a reboot.

**Commands:**
```
R1(config)# exit
R1# copy running-config startup-config
R1#
```

Or use the shortcut:
```
R1# write memory
```

**Explanation:**
- `copy running-config startup-config` (or `wr` for short) saves the active configuration to NVRAM
- The running configuration is what's currently active in RAM
- The startup configuration loads when the router boots

## Step 9: Verify Interface Configuration

Use show commands to verify your configuration.

**Commands:**
```
R1# show ip interface brief
```

**Expected Output:**
```
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual up                    up
GigabitEthernet0/1     192.168.2.1     YES manual up                    up
```

**Additional Verification Commands:**
```
R1# show running-config
R1# show interfaces gigabitethernet 0/0
R1# show ip interface gigabitethernet 0/0
```

## Step 10: Test Connectivity

If you have devices connected to the interfaces, test connectivity.

**Commands:**
```
R1# ping 192.168.1.10
R1# ping 192.168.2.10
```

**Expected Output:**
```
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 192.168.1.10, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms
```

## Common Issues and Troubleshooting

### Interface Shows "administratively down"
**Problem:** You forgot to use `no shutdown`
**Solution:**
```
R1(config)# interface g0/0
R1(config-if)# no shutdown
```

### Interface Shows "down/down"
**Problem:** No cable connected or cable fault
**Solution:** Check physical connections

### Ping Fails
**Problem:** Could be IP addressing, subnet mask, or connectivity issues
**Solution:**
1. Verify IP addresses: `show ip interface brief`
2. Check subnet masks match
3. Verify cable connections
4. Check for firewall/access list blocking

## Key Concepts

### IP Addressing
- Each interface needs a unique IP address
- Subnet mask defines the network portion of the address
- Devices on the same subnet can communicate directly

### Interface States
- up/up: Interface is operational
- up/down: Physical layer up, data link layer down
- administratively down: Interface is shutdown

### Configuration Modes
1. User EXEC (>): Limited show commands
2. Privileged EXEC (#): All show commands, limited configuration
3. Global Configuration (config)#: System-wide settings
4. Interface Configuration (config-if)#: Interface-specific settings

## Practice Exercises

1. Configure a third interface (if available) with IP 192.168.3.1/24
2. Change the hostname to "Border-Router"
3. Add descriptions to all interfaces
4. Practice using show commands to verify configuration
5. Intentionally shutdown an interface, then bring it back up

## Summary

In this lab, you learned to:
- Navigate Cisco IOS command modes
- Configure basic router settings (hostname, passwords)
- Assign IP addresses to interfaces
- Activate interfaces using `no shutdown`
- Save configurations
- Verify configuration using show commands
- Test connectivity with ping

These are foundational skills for all networking labs that follow.
