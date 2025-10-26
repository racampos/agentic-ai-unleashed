# Lab 2: Static Routing Configuration

## Lab Objectives
- Understand the purpose of routing
- Configure static routes on Cisco routers
- Verify routing table entries
- Test end-to-end connectivity between different networks

## Lab Topology
- Router R1:
  - G0/0: 192.168.1.1/24 (LAN 1)
  - G0/1: 10.0.0.1/30 (WAN link to R2)
- Router R2:
  - G0/0: 10.0.0.2/30 (WAN link to R1)
  - G0/1: 192.168.2.1/24 (LAN 2)

## Prerequisites
- Completion of Lab 1 (Basic Router Configuration)
- Understanding of IP routing concepts
- Knowledge of subnet masks and network addresses

## Routing Fundamentals

### What is Routing?
Routing is the process of forwarding packets between different networks. Routers make forwarding decisions based on their routing table.

### Types of Routes
1. **Directly Connected**: Networks directly attached to router interfaces
2. **Static Routes**: Manually configured by administrator
3. **Dynamic Routes**: Learned automatically via routing protocols

### When to Use Static Routes
- Small networks with few routers
- Stub networks (networks with only one exit point)
- Default routes to the Internet
- When you need complete control over routing

## Step 1: Verify Current Routing Table on R1

Before adding routes, examine the existing routing table.

**Commands:**
```
R1# show ip route
```

**Expected Output:**
```
Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area

Gateway of last resort is not set

C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
C    10.0.0.0/30 is directly connected, GigabitEthernet0/1
```

**Explanation:**
- The "C" code indicates directly connected networks
- R1 knows about its own subnets but doesn't know how to reach 192.168.2.0/24

## Step 2: Configure Static Route on R1

Add a static route to tell R1 how to reach the 192.168.2.0/24 network.

**Commands:**
```
R1# configure terminal
R1(config)# ip route 192.168.2.0 255.255.255.0 10.0.0.2
R1(config)# exit
R1#
```

**Explanation:**
- `ip route` command syntax: `ip route [destination-network] [subnet-mask] [next-hop-ip]`
- Destination: 192.168.2.0/24 (the remote network)
- Next-hop: 10.0.0.2 (R2's interface on the WAN link)
- This tells R1: "To reach 192.168.2.0/24, send packets to 10.0.0.2"

**Alternative Syntax (Exit Interface):**
```
R1(config)# ip route 192.168.2.0 255.255.255.0 gigabitethernet 0/1
```

## Step 3: Verify Static Route on R1

Check that the route appears in the routing table.

**Commands:**
```
R1# show ip route
```

**Expected Output:**
```
Gateway of last resort is not set

C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
C    10.0.0.0/30 is directly connected, GigabitEthernet0/1
S    192.168.2.0/24 [1/0] via 10.0.0.2
```

**Explanation:**
- The "S" code indicates a static route
- [1/0] shows administrative distance (1) and metric (0)
- "via 10.0.0.2" shows the next-hop address

## Step 4: Configure Static Route on R2

R2 also needs a route to reach R1's LAN.

**Commands:**
```
R2# configure terminal
R2(config)# ip route 192.168.1.0 255.255.255.0 10.0.0.1
R2(config)# exit
R2#
```

**Explanation:**
- R2 needs to know how to reach 192.168.1.0/24
- Traffic destined for 192.168.1.0/24 should be sent to 10.0.0.1 (R1)

## Step 5: Verify Static Route on R2

**Commands:**
```
R2# show ip route
```

**Expected Output:**
```
C    10.0.0.0/30 is directly connected, GigabitEthernet0/0
C    192.168.2.0/24 is directly connected, GigabitEthernet0/1
S    192.168.1.0/24 [1/0] via 10.0.0.1
```

## Step 6: Test End-to-End Connectivity

From R1, ping a device on R2's LAN (or R2's G0/1 interface).

**Commands:**
```
R1# ping 192.168.2.1
```

**Expected Output:**
```
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 192.168.2.1, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms
```

**From R2, ping R1's LAN:**
```
R2# ping 192.168.1.1
```

## Step 7: Configure a Default Route (Optional)

A default route is used when no specific route matches the destination.

**Commands:**
```
R1(config)# ip route 0.0.0.0 0.0.0.0 10.0.0.2
```

**Explanation:**
- 0.0.0.0 0.0.0.0 matches any destination
- This is a "gateway of last resort"
- Commonly used for Internet access

**Verify Default Route:**
```
R1# show ip route
```

**Expected Output:**
```
Gateway of last resort is 10.0.0.2 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 10.0.0.2
```

The asterisk (*) indicates this is the default route.

## Step 8: Save Configuration

Don't forget to save on both routers!

**Commands:**
```
R1# write memory
R2# write memory
```

## Troubleshooting Static Routes

### Ping Fails Despite Correct Routes

**Possible Causes:**
1. **Missing return route**: R1 has a route to R2's network, but R2 doesn't have a route back
2. **Interface down**: Check `show ip interface brief`
3. **Wrong next-hop IP**: Verify next-hop is reachable
4. **Wrong subnet mask**: Double-check subnet masks

**Diagnostic Commands:**
```
R1# show ip route [destination-ip]
R1# ping [next-hop-ip]
R1# traceroute [destination-ip]
```

### Route Not Appearing in Routing Table

**Possible Causes:**
1. **Next-hop unreachable**: Next-hop must be directly connected
2. **Interface down**: The exit interface must be up/up
3. **Typo in command**: Verify syntax

**Check Next-Hop Reachability:**
```
R1# ping 10.0.0.2
```

If the next-hop isn't reachable, the static route won't be installed.

## Key Concepts

### Routing Table Lookup Process
1. Router receives packet
2. Checks destination IP
3. Looks for most specific match in routing table
4. Forwards packet out appropriate interface to next-hop
5. If no match, drops packet (or uses default route if configured)

### Administrative Distance
- Indicates trustworthiness of route source
- Lower is better
- Static routes: AD = 1
- Directly connected: AD = 0

### Next-Hop vs Exit Interface
**Next-Hop (Recommended for Ethernet):**
```
ip route 192.168.2.0 255.255.255.0 10.0.0.2
```

**Exit Interface:**
```
ip route 192.168.2.0 255.255.255.0 gigabitethernet 0/1
```

**Both (Most specific):**
```
ip route 192.168.2.0 255.255.255.0 gigabitethernet 0/1 10.0.0.2
```

## Practice Exercises

1. Add a third router (R3) and configure static routes for three-router connectivity
2. Configure a default route on R1 pointing to R2
3. Use traceroute to see the path packets take
4. Intentionally misconfigure a route and observe the behavior
5. Remove a static route using `no ip route ...`

## Advanced: Floating Static Routes

Floating static routes provide backup paths with higher administrative distance.

**Commands:**
```
R1(config)# ip route 192.168.2.0 255.255.255.0 10.0.0.2
R1(config)# ip route 192.168.2.0 255.255.255.0 10.0.1.2 5
```

The second route has AD=5, so it's only used if the first fails.

## Summary

In this lab, you learned to:
- View the routing table with `show ip route`
- Configure static routes with `ip route` command
- Use next-hop IP addresses for route configuration
- Configure default routes (gateway of last resort)
- Test connectivity across multiple routers
- Troubleshoot routing issues
- Understand routing table lookup process

Static routing provides the foundation for understanding all routing concepts!
