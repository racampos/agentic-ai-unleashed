# Cisco IOS Command Reference

## Show Commands

### Interface Information

**show ip interface brief**
- Shows summary of all interfaces with IP addresses, status, and protocol
- Output format: Interface | IP-Address | OK? | Method | Status | Protocol
- Example: `show ip interface brief`

**show interface [interface-name]**
- Shows detailed information about a specific interface
- Example: `show interface GigabitEthernet0/0`
- Shows: MTU, BW, DLY, reliability, load, encapsulation, duplex, speed, input/output packets

**show ip interface [interface-name]**
- Shows IP-specific interface information
- Example: `show ip interface GigabitEthernet0/0`
- Shows: IP address, subnet mask, helper addresses, security level, ICMP settings

### Configuration Commands

**show running-config**
- Displays the current running configuration
- Example: `show running-config`

**show running-config interface [interface-name]**
- Shows running configuration for a specific interface
- Example: `show running-config interface GigabitEthernet0/0`
- Shows: Interface config including IP address, description, shutdown status

**show startup-config**
- Displays the startup configuration stored in NVRAM
- Example: `show startup-config`

### Routing Information

**show ip route**
- Displays the IP routing table
- Shows all routes (connected, static, dynamic)
- Route codes: C (connected), S (static), R (RIP), O (OSPF), D (EIGRP)
- Example: `show ip route`

**show ip route [network]**
- Shows routing information for a specific network
- Example: `show ip route 192.168.1.0`

**show ip protocols**
- Shows IP routing protocol information
- Displays routing protocols running and their parameters
- Example: `show ip protocols`

### VLAN Commands (for Switches)

**show vlan**
- Shows VLAN database information
- Displays VLAN ID, name, status, and ports
- Example: `show vlan brief`

**show vlan id [vlan-id]**
- Shows information about a specific VLAN
- Example: `show vlan id 10`

### System Information

**show version**
- Displays system hardware and software status
- Shows: IOS version, uptime, configuration register, memory, interfaces
- Example: `show version`

**show clock**
- Displays the system clock
- Example: `show clock`

**show processes**
- Displays information about active processes
- Example: `show processes cpu`

## Configuration Mode Commands

### Entering Configuration Modes

**configure terminal**
- Enters global configuration mode from privileged EXEC mode
- Shortcut: `conf t`
- Prompt changes to: `Router(config)#`

**interface [interface-name]**
- Enters interface configuration mode
- Example: `interface GigabitEthernet0/0`
- Prompt changes to: `Router(config-if)#`

**router [protocol]**
- Enters router configuration mode for routing protocol
- Example: `router ospf 1`
- Prompt changes to: `Router(config-router)#`

### Interface Configuration

**ip address [address] [mask]**
- Configures IP address and subnet mask on an interface
- Must be in interface configuration mode
- Example: `ip address 192.168.1.1 255.255.255.0`

**no shutdown**
- Enables an interface (brings it up)
- Example: `no shutdown`
- Shortcut: `no shut`

**shutdown**
- Administratively disables an interface
- Example: `shutdown`
- Shortcut: `shut`

**description [text]**
- Adds a description to an interface
- Example: `description Link to Core Switch`

**speed [10|100|1000|auto]**
- Sets interface speed
- Example: `speed 1000`

**duplex [full|half|auto]**
- Sets duplex mode
- Example: `duplex full`

### Static Routing

**ip route [network] [mask] [next-hop | exit-interface]**
- Configures a static route
- Example: `ip route 10.0.0.0 255.0.0.0 192.168.1.2`
- Example: `ip route 10.0.0.0 255.0.0.0 GigabitEthernet0/1`

**no ip route [network] [mask] [next-hop]**
- Removes a static route
- Example: `no ip route 10.0.0.0 255.0.0.0 192.168.1.2`

### Saving Configuration

**copy running-config startup-config**
- Saves running configuration to startup configuration
- Shortcut: `copy run start` or `wr` (write memory)
- Example: `copy running-config startup-config`

**write memory**
- Legacy command to save configuration
- Shortcut: `wr`
- Equivalent to `copy running-config startup-config`

### Hostname and Passwords

**hostname [name]**
- Sets the router/switch hostname
- Example: `hostname Router1`

**enable secret [password]**
- Sets encrypted enable password
- Example: `enable secret cisco123`
- Recommended over `enable password`

**enable password [password]**
- Sets unencrypted enable password
- Example: `enable password cisco`
- Not recommended - use `enable secret` instead

### Line Configuration

**line console 0**
- Enters console line configuration mode
- Used to configure console access
- Example: `line console 0`

**line vty 0 4**
- Enters vty line configuration mode for Telnet/SSH
- Example: `line vty 0 4`

**password [password]**
- Sets password for line (console or vty)
- Example: `password cisco`

**login**
- Enables password checking on line
- Example: `login`

## Verification Commands

**ping [address]**
- Tests network connectivity
- Example: `ping 192.168.1.1`
- Example: `ping 8.8.8.8`

**traceroute [address]**
- Traces route to destination
- Example: `traceroute 8.8.8.8`

## Common Command Syntax Rules

1. Commands are case-insensitive
2. Use Tab for command completion
3. Use `?` for help at any point
4. Use `do` prefix to run EXEC commands from config mode
   - Example: `do show ip interface brief` (from config mode)

## Command Abbreviations

- `conf t` = `configure terminal`
- `int` = `interface`
- `no shut` = `no shutdown`
- `wr` = `write memory`
- `copy run start` = `copy running-config startup-config`
- `sh` = `show`

## Common Mistakes to Avoid

❌ WRONG: `show running interface GigabitEthernet0/0 ip address` (This command doesn't exist!)
✅ CORRECT: `show running-config interface GigabitEthernet0/0`

❌ WRONG: `show ip GigabitEthernet0/0` (Incomplete command)
✅ CORRECT: `show ip interface GigabitEthernet0/0`

❌ WRONG: `config interface Gi0/0` (Wrong mode entry)
✅ CORRECT: `configure terminal` then `interface GigabitEthernet0/0`

## Notes

- Interface names can be abbreviated (e.g., Gi0/0 for GigabitEthernet0/0, Fa0/1 for FastEthernet0/1)
- Always save configuration with `copy running-config startup-config` to persist changes across reboots
- Use `no` prefix to negate/remove configuration commands
- Many commands have shorter aliases for convenience
